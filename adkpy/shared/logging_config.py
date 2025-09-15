"""
Logging Configuration

Standardized logging setup for all agents and services.
"""

from __future__ import annotations

import asyncio
import json
import logging
import logging.handlers
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import colorlog


# --- Logging Configuration ---

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FORMAT_DETAILED = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
LOG_FORMAT_JSON = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "file": "%(filename)s", "line": %(lineno)d}'

COLOR_LOG_FORMAT = "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s - %(message)s"

LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red,bg_white",
}


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False,
    colorize: bool = True,
    log_dir: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
):
    """
    Setup logging configuration.

    Args:
        level: Logging level
        log_file: Log file path
        json_format: Use JSON format
        colorize: Use colored output for console
        log_dir: Directory for log files
        max_bytes: Max size for rotating logs
        backup_count: Number of backup files
    """
    # Convert level string to logging level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if json_format:
        console_formatter = logging.Formatter(LOG_FORMAT_JSON)
    elif colorize and sys.stdout.isatty():
        console_formatter = colorlog.ColoredFormatter(
            COLOR_LOG_FORMAT,
            log_colors=LOG_COLORS,
        )
    else:
        console_formatter = logging.Formatter(LOG_FORMAT)

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler
    if log_file or log_dir:
        if log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"adk_{datetime.now():%Y%m%d}.log"
        else:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setLevel(log_level)

        file_formatter = logging.Formatter(
            LOG_FORMAT_JSON if json_format else LOG_FORMAT_DETAILED
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured: level={level}, "
        f"file={log_file}, json={json_format}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# --- Logging Context Manager ---

class LogContext:
    """Context manager for structured logging."""

    def __init__(
        self,
        logger: logging.Logger,
        operation: str,
        **context_data
    ):
        """
        Initialize log context.

        Args:
            logger: Logger instance
            operation: Operation name
            **context_data: Context data to log
        """
        self.logger = logger
        self.operation = operation
        self.context_data = context_data
        self.start_time = None

    def __enter__(self):
        """Enter context."""
        self.start_time = time.time()
        self.logger.info(
            f"Starting {self.operation}",
            extra={"context": self.context_data}
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        duration = time.time() - self.start_time

        if exc_type:
            self.logger.error(
                f"Failed {self.operation} after {duration:.2f}s: {exc_val}",
                exc_info=True,
                extra={
                    "context": self.context_data,
                    "duration": duration,
                }
            )
        else:
            self.logger.info(
                f"Completed {self.operation} in {duration:.2f}s",
                extra={
                    "context": self.context_data,
                    "duration": duration,
                }
            )

    def update(self, **updates):
        """Update context data."""
        self.context_data.update(updates)


@contextmanager
def log_context(
    logger: logging.Logger,
    operation: str,
    **context_data
):
    """
    Context manager for structured logging.

    Args:
        logger: Logger instance
        operation: Operation name
        **context_data: Context data

    Example:
        with log_context(logger, "process_request", user_id="123"):
            # Process request
            pass
    """
    context = LogContext(logger, operation, **context_data)
    try:
        yield context
    finally:
        pass  # Cleanup handled in __exit__


# --- Logging Decorators ---

def log_timing(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
):
    """
    Decorator to log function execution time.

    Args:
        logger: Logger instance (uses function module logger if None)
        level: Logging level
    """
    def decorator(func: Callable) -> Callable:
        func_logger = logger or logging.getLogger(func.__module__)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            try:
                func_logger.log(
                    level,
                    f"Starting {func_name}",
                    extra={"function": func_name}
                )

                result = await func(*args, **kwargs)

                duration = time.time() - start_time
                func_logger.log(
                    level,
                    f"Completed {func_name} in {duration:.3f}s",
                    extra={
                        "function": func_name,
                        "duration": duration,
                    }
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                func_logger.error(
                    f"Failed {func_name} after {duration:.3f}s: {e}",
                    exc_info=True,
                    extra={
                        "function": func_name,
                        "duration": duration,
                    }
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = func.__name__

            try:
                func_logger.log(
                    level,
                    f"Starting {func_name}",
                    extra={"function": func_name}
                )

                result = func(*args, **kwargs)

                duration = time.time() - start_time
                func_logger.log(
                    level,
                    f"Completed {func_name} in {duration:.3f}s",
                    extra={
                        "function": func_name,
                        "duration": duration,
                    }
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                func_logger.error(
                    f"Failed {func_name} after {duration:.3f}s: {e}",
                    exc_info=True,
                    extra={
                        "function": func_name,
                        "duration": duration,
                    }
                )
                raise

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_error(
    logger: Optional[logging.Logger] = None,
    reraise: bool = True,
):
    """
    Decorator to log errors.

    Args:
        logger: Logger instance
        reraise: Whether to reraise exceptions
    """
    def decorator(func: Callable) -> Callable:
        func_logger = logger or logging.getLogger(func.__module__)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                func_logger.error(
                    f"Error in {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        "function": func.__name__,
                        "error_type": type(e).__name__,
                    }
                )
                if reraise:
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_logger.error(
                    f"Error in {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        "function": func.__name__,
                        "error_type": type(e).__name__,
                    }
                )
                if reraise:
                    raise

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# --- Structured Logging ---

class StructuredLogger:
    """Logger wrapper for structured logging."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize structured logger.

        Args:
            logger: Base logger
        """
        self.logger = logger
        self.context: Dict[str, Any] = {}

    def with_context(self, **context) -> StructuredLogger:
        """
        Create logger with additional context.

        Args:
            **context: Context data

        Returns:
            New logger with context
        """
        new_logger = StructuredLogger(self.logger)
        new_logger.context = {**self.context, **context}
        return new_logger

    def _format_message(
        self,
        message: str,
        **kwargs
    ) -> tuple[str, Dict[str, Any]]:
        """Format message with context."""
        extra = {
            **self.context,
            **kwargs,
        }

        # Add timestamp
        extra["timestamp"] = datetime.utcnow().isoformat()

        return message, {"extra": extra}

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        msg, extra = self._format_message(message, **kwargs)
        self.logger.debug(msg, **extra)

    def info(self, message: str, **kwargs):
        """Log info message."""
        msg, extra = self._format_message(message, **kwargs)
        self.logger.info(msg, **extra)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        msg, extra = self._format_message(message, **kwargs)
        self.logger.warning(msg, **extra)

    def error(self, message: str, exc_info=False, **kwargs):
        """Log error message."""
        msg, extra = self._format_message(message, **kwargs)
        self.logger.error(msg, exc_info=exc_info, **extra)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        msg, extra = self._format_message(message, **kwargs)
        self.logger.critical(msg, **extra)


def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get structured logger.

    Args:
        name: Logger name

    Returns:
        Structured logger
    """
    return StructuredLogger(logging.getLogger(name))