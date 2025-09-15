"""
Telemetry Tracking

Shared telemetry utilities for tracking agent usage and performance.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from .schemas import TelemetryData, MetricsData

logger = logging.getLogger(__name__)


# --- Telemetry Storage ---

class TelemetryStore:
    """In-memory telemetry storage with aggregation."""

    def __init__(self, max_events: int = 10000):
        """
        Initialize telemetry store.

        Args:
            max_events: Maximum events to keep in memory
        """
        self.max_events = max_events
        self.events: List[TelemetryData] = []
        self.metrics: List[MetricsData] = []
        self.aggregates: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = asyncio.Lock()

    async def add_event(self, event: TelemetryData):
        """Add telemetry event."""
        async with self._lock:
            self.events.append(event)

            # Trim if needed
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]

            # Update aggregates
            self._update_aggregates(event)

    async def add_metric(self, metric: MetricsData):
        """Add metric data."""
        async with self._lock:
            self.metrics.append(metric)

            # Trim if needed
            if len(self.metrics) > self.max_events:
                self.metrics = self.metrics[-self.max_events:]

    def _update_aggregates(self, event: TelemetryData):
        """Update aggregate statistics."""
        agent = event.agent_name

        if agent not in self.aggregates:
            self.aggregates[agent] = {
                "total_calls": 0,
                "total_tokens": 0,
                "total_duration_ms": 0,
                "total_cost": 0.0,
                "errors": 0,
                "models_used": set(),
            }

        stats = self.aggregates[agent]
        stats["total_calls"] += 1
        stats["total_tokens"] += event.total_tokens
        stats["total_duration_ms"] += event.duration_ms
        stats["total_cost"] += event.cost or 0.0

        if event.model:
            stats["models_used"].add(event.model)

    async def get_summary(
        self,
        agent_name: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get telemetry summary.

        Args:
            agent_name: Filter by agent name
            since: Filter events since timestamp

        Returns:
            Summary statistics
        """
        async with self._lock:
            # Filter events
            events = self.events

            if agent_name:
                events = [e for e in events if e.agent_name == agent_name]

            if since:
                since_ts = since.timestamp()
                events = [e for e in events if e.timestamp >= since_ts]

            if not events:
                return {
                    "total_events": 0,
                    "agents": [],
                    "total_tokens": 0,
                    "total_duration_ms": 0,
                    "total_cost": 0.0,
                }

            # Calculate summary
            agent_stats = defaultdict(lambda: {
                "calls": 0,
                "tokens": 0,
                "duration_ms": 0,
                "cost": 0.0,
            })

            for event in events:
                stats = agent_stats[event.agent_name]
                stats["calls"] += 1
                stats["tokens"] += event.total_tokens
                stats["duration_ms"] += event.duration_ms
                stats["cost"] += event.cost or 0.0

            return {
                "total_events": len(events),
                "agents": dict(agent_stats),
                "total_tokens": sum(e.total_tokens for e in events),
                "total_duration_ms": sum(e.duration_ms for e in events),
                "total_cost": sum(e.cost or 0.0 for e in events),
                "time_range": {
                    "start": min(e.timestamp for e in events),
                    "end": max(e.timestamp for e in events),
                },
            }

    async def clear(self):
        """Clear all telemetry data."""
        async with self._lock:
            self.events.clear()
            self.metrics.clear()
            self.aggregates.clear()


# --- Global Telemetry Tracker ---

class TelemetryTracker:
    """Global telemetry tracker singleton."""

    _instance: Optional[TelemetryTracker] = None
    _store: Optional[TelemetryStore] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._store = TelemetryStore()
        return cls._instance

    @classmethod
    def get_store(cls) -> TelemetryStore:
        """Get telemetry store."""
        if cls._store is None:
            cls._store = TelemetryStore()
        return cls._store

    @classmethod
    async def track(
        cls,
        agent_name: str,
        operation: str,
        duration_ms: int,
        model: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Track telemetry event.

        Args:
            agent_name: Name of the agent
            operation: Operation performed
            duration_ms: Duration in milliseconds
            model: Model used
            prompt_tokens: Prompt tokens used
            completion_tokens: Completion tokens used
            cost: Estimated cost
            metadata: Additional metadata
        """
        event = TelemetryData(
            agent_name=agent_name,
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_ms=duration_ms,
            cost=cost,
            timestamp=time.time(),
            metadata=metadata or {},
        )

        store = cls.get_store()
        await store.add_event(event)

        logger.debug(
            f"Telemetry: {agent_name}.{operation} - "
            f"{prompt_tokens + completion_tokens} tokens, "
            f"{duration_ms}ms"
        )

    @classmethod
    async def track_metric(
        cls,
        metric_name: str,
        value: float,
        unit: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Track metric data.

        Args:
            metric_name: Metric name
            value: Metric value
            unit: Metric unit
            tags: Metric tags
        """
        metric = MetricsData(
            metric_name=metric_name,
            value=value,
            unit=unit,
            tags=tags or {},
            timestamp=time.time(),
        )

        store = cls.get_store()
        await store.add_metric(metric)

    @classmethod
    async def get_summary(
        cls,
        agent_name: Optional[str] = None,
        since_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get telemetry summary.

        Args:
            agent_name: Filter by agent
            since_hours: Include events from last N hours

        Returns:
            Summary statistics
        """
        since = None
        if since_hours:
            since = datetime.utcnow() - timedelta(hours=since_hours)

        store = cls.get_store()
        return await store.get_summary(agent_name, since)

    @classmethod
    async def clear(cls):
        """Clear all telemetry data."""
        store = cls.get_store()
        await store.clear()


# --- Decorator Functions ---

def track_usage(
    agent_name: str,
    operation: Optional[str] = None,
):
    """
    Decorator to track function usage.

    Args:
        agent_name: Agent name
        operation: Operation name (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            op_name = operation or func.__name__

            try:
                result = await func(*args, **kwargs)

                # Extract telemetry from result if available
                tokens = 0
                model = None
                cost = None

                if hasattr(result, "usage"):
                    usage = result.usage
                    if hasattr(usage, "prompt_tokens"):
                        tokens += usage.prompt_tokens
                    if hasattr(usage, "completion_tokens"):
                        tokens += usage.completion_tokens
                    if hasattr(usage, "model"):
                        model = usage.model

                # Track telemetry
                duration_ms = int((time.time() - start_time) * 1000)
                await TelemetryTracker.track(
                    agent_name=agent_name,
                    operation=op_name,
                    duration_ms=duration_ms,
                    model=model,
                    prompt_tokens=tokens // 2,  # Estimate
                    completion_tokens=tokens // 2,  # Estimate
                    cost=cost,
                )

                return result

            except Exception as e:
                # Track error
                duration_ms = int((time.time() - start_time) * 1000)
                await TelemetryTracker.track(
                    agent_name=agent_name,
                    operation=op_name,
                    duration_ms=duration_ms,
                    metadata={"error": str(e)},
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            op_name = operation or func.__name__

            try:
                result = func(*args, **kwargs)

                # Track telemetry (fire and forget)
                duration_ms = int((time.time() - start_time) * 1000)
                asyncio.create_task(
                    TelemetryTracker.track(
                        agent_name=agent_name,
                        operation=op_name,
                        duration_ms=duration_ms,
                    )
                )

                return result

            except Exception as e:
                # Track error
                duration_ms = int((time.time() - start_time) * 1000)
                asyncio.create_task(
                    TelemetryTracker.track(
                        agent_name=agent_name,
                        operation=op_name,
                        duration_ms=duration_ms,
                        metadata={"error": str(e)},
                    )
                )
                raise

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def track_event(
    agent_name: str,
    event_type: str,
    data: Any = None,
):
    """
    Track a custom event.

    Args:
        agent_name: Agent name
        event_type: Event type
        data: Event data
    """
    await TelemetryTracker.track(
        agent_name=agent_name,
        operation=f"event.{event_type}",
        duration_ms=0,
        metadata={"event_data": data} if data else None,
    )


async def track_error(
    agent_name: str,
    operation: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Track an error.

    Args:
        agent_name: Agent name
        operation: Operation that failed
        error: Exception that occurred
        context: Additional context
    """
    metadata = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    if context:
        metadata["context"] = context

    await TelemetryTracker.track(
        agent_name=agent_name,
        operation=f"error.{operation}",
        duration_ms=0,
        metadata=metadata,
    )

    logger.error(
        f"{agent_name}.{operation} error: {error}",
        exc_info=True,
        extra={"context": context}
    )


async def get_telemetry_summary(
    agent_name: Optional[str] = None,
    since_hours: int = 24,
) -> Dict[str, Any]:
    """
    Get telemetry summary.

    Args:
        agent_name: Filter by agent
        since_hours: Include events from last N hours

    Returns:
        Summary statistics
    """
    return await TelemetryTracker.get_summary(agent_name, since_hours)


# --- Cost Estimation ---

class CostEstimator:
    """Estimate costs for model usage."""

    # Cost per 1M tokens (example rates)
    MODEL_COSTS = {
        "gemini-2.5-flash": {"input": 0.0375, "output": 0.15},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    @classmethod
    def estimate_cost(
        cls,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Estimate cost for token usage.

        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in dollars
        """
        # Find model costs
        costs = None
        for model_key in cls.MODEL_COSTS:
            if model_key in model.lower():
                costs = cls.MODEL_COSTS[model_key]
                break

        if not costs:
            # Default costs if model not found
            costs = {"input": 1.0, "output": 2.0}

        # Calculate cost
        input_cost = (prompt_tokens / 1_000_000) * costs["input"]
        output_cost = (completion_tokens / 1_000_000) * costs["output"]

        return round(input_cost + output_cost, 6)