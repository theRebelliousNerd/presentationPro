"""
Session Management for Presentation Generation

Manages presentation sessions, tracks workflow state, stores intermediate
results, and provides persistence across the multi-agent pipeline.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from threading import Lock

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Session lifecycle states."""
    CREATED = "created"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    EXPIRED = "expired"


class PresentationSession(BaseModel):
    """
    Represents a presentation generation session.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    presentation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: SessionState = SessionState.CREATED
    workflow_state: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # Workflow data
    refined_goals: Optional[str] = None
    outline: Optional[Dict[str, Any]] = None
    slides: Dict[int, Dict[str, Any]] = Field(default_factory=dict)
    research: Optional[Dict[str, Any]] = None
    script: Optional[str] = None

    # Results from agents
    results: Dict[str, Any] = Field(default_factory=dict)

    # Error tracking
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Usage tracking
    usage: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def update_state(self, workflow_state: str):
        """Update workflow state."""
        self.workflow_state = workflow_state
        self.updated_at = datetime.utcnow()
        if self.state == SessionState.CREATED:
            self.state = SessionState.ACTIVE

    def add_result(self, agent_name: str, result: Any):
        """Add agent result."""
        self.results[agent_name] = result
        self.updated_at = datetime.utcnow()

        # Update usage if present
        if isinstance(result, dict) and "usage" in result:
            self._update_usage(agent_name, result["usage"])

    def add_slide(self, slide_number: int, slide_data: Dict[str, Any]):
        """Add a slide to the presentation."""
        self.slides[slide_number] = slide_data
        self.updated_at = datetime.utcnow()

    def add_error(self, error_message: str, details: Optional[Dict[str, Any]] = None):
        """Add an error to the session."""
        self.errors.append({
            "message": error_message,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.state = SessionState.ERROR
        self.updated_at = datetime.utcnow()

    def complete(self):
        """Mark session as complete."""
        self.state = SessionState.COMPLETED
        self.updated_at = datetime.utcnow()

    def expire(self):
        """Mark session as expired."""
        self.state = SessionState.EXPIRED
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if session is active."""
        return self.state == SessionState.ACTIVE

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.state == SessionState.EXPIRED:
            return True
        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.expire()
            return True
        return False

    def get_presentation_data(self) -> Dict[str, Any]:
        """Get complete presentation data."""
        return {
            "id": self.presentation_id,
            "refined_goals": self.refined_goals,
            "outline": self.outline,
            "slides": self.slides,
            "research": self.research,
            "script": self.script,
            "metadata": self.metadata
        }

    def _update_usage(self, agent_name: str, usage_data: Dict[str, Any]):
        """Update usage statistics."""
        if agent_name not in self.usage:
            self.usage[agent_name] = {}

        # Aggregate token counts
        for key, value in usage_data.items():
            if isinstance(value, (int, float)):
                if key not in self.usage[agent_name]:
                    self.usage[agent_name][key] = 0
                self.usage[agent_name][key] += value

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "presentation_id": self.presentation_id,
            "state": self.state,
            "workflow_state": self.workflow_state,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "refined_goals": self.refined_goals,
            "outline": self.outline,
            "slides": self.slides,
            "research": self.research,
            "script": self.script,
            "results": self.results,
            "errors": self.errors,
            "metadata": self.metadata,
            "usage": self.usage
        }


class SessionManager:
    """
    Manages presentation sessions with persistence and lifecycle management.
    """

    def __init__(
        self,
        max_sessions: int = 1000,
        session_ttl_hours: int = 24,
        cleanup_interval_minutes: int = 30
    ):
        """
        Initialize session manager.

        Args:
            max_sessions: Maximum number of sessions to keep
            session_ttl_hours: Session time-to-live in hours
            cleanup_interval_minutes: Cleanup interval in minutes
        """
        self.max_sessions = max_sessions
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)

        self.sessions: Dict[str, PresentationSession] = {}
        self.lock = Lock()

        self.last_cleanup = datetime.utcnow()

        logger.info(f"Session manager initialized (max: {max_sessions}, TTL: {session_ttl_hours}h)")

    def create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PresentationSession:
        """
        Create a new session.

        Args:
            session_id: Optional session ID
            user_id: Optional user ID
            metadata: Optional metadata

        Returns:
            Created session
        """
        with self.lock:
            # Check if we need cleanup
            self._maybe_cleanup()

            # Check max sessions
            if len(self.sessions) >= self.max_sessions:
                self._evict_oldest()

            # Create session
            session = PresentationSession(
                id=session_id or str(uuid.uuid4()),
                user_id=user_id,
                expires_at=datetime.utcnow() + self.session_ttl,
                metadata=metadata or {}
            )

            self.sessions[session.id] = session

            logger.info(f"Created session: {session.id} for user: {user_id}")
            return session

    def get_session(self, session_id: str) -> Optional[PresentationSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found and not expired
        """
        with self.lock:
            session = self.sessions.get(session_id)

            if session:
                if session.is_expired():
                    logger.info(f"Session expired: {session_id}")
                    del self.sessions[session_id]
                    return None
                return session

            return None

    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """
        Update session fields.

        Args:
            session_id: Session identifier
            updates: Fields to update
        """
        with self.lock:
            session = self.sessions.get(session_id)
            if session:
                for key, value in updates.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                session.updated_at = datetime.utcnow()
                logger.debug(f"Updated session: {session_id}")

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            return False

    def list_sessions(
        self,
        user_id: Optional[str] = None,
        state: Optional[SessionState] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List sessions with optional filters.

        Args:
            user_id: Filter by user ID
            state: Filter by state
            limit: Maximum number of results

        Returns:
            List of session summaries
        """
        with self.lock:
            sessions = []

            for session in self.sessions.values():
                # Apply filters
                if user_id and session.user_id != user_id:
                    continue
                if state and session.state != state:
                    continue

                # Add summary
                sessions.append({
                    "id": session.id,
                    "user_id": session.user_id,
                    "presentation_id": session.presentation_id,
                    "state": session.state,
                    "workflow_state": session.workflow_state,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "slide_count": len(session.slides),
                    "has_outline": session.outline is not None,
                    "has_script": session.script is not None,
                    "error_count": len(session.errors)
                })

                if len(sessions) >= limit:
                    break

            # Sort by update time (most recent first)
            sessions.sort(key=lambda x: x["updated_at"], reverse=True)

            return sessions

    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        with self.lock:
            return [
                session_id
                for session_id, session in self.sessions.items()
                if session.is_active()
            ]

    def count_active(self) -> int:
        """Count active sessions."""
        with self.lock:
            return sum(
                1 for session in self.sessions.values()
                if session.is_active()
            )

    def count_total(self) -> int:
        """Count total sessions."""
        return len(self.sessions)

    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        with self.lock:
            states = {}
            for session in self.sessions.values():
                state = session.state
                if state not in states:
                    states[state] = 0
                states[state] += 1

            return {
                "total": len(self.sessions),
                "by_state": states,
                "active": states.get(SessionState.ACTIVE, 0),
                "completed": states.get(SessionState.COMPLETED, 0),
                "error": states.get(SessionState.ERROR, 0),
                "expired": states.get(SessionState.EXPIRED, 0)
            }

    def _maybe_cleanup(self):
        """Run cleanup if needed."""
        now = datetime.utcnow()
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired()
            self.last_cleanup = now

    def _cleanup_expired(self):
        """Remove expired sessions."""
        expired = []

        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired.append(session_id)

        for session_id in expired:
            del self.sessions[session_id]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def _evict_oldest(self):
        """Evict oldest inactive session."""
        # Find oldest non-active session
        oldest_id = None
        oldest_time = datetime.utcnow()

        for session_id, session in self.sessions.items():
            if not session.is_active() and session.updated_at < oldest_time:
                oldest_id = session_id
                oldest_time = session.updated_at

        if oldest_id:
            del self.sessions[oldest_id]
            logger.info(f"Evicted oldest session: {oldest_id}")
        else:
            # No inactive sessions, evict oldest active
            if self.sessions:
                oldest_id = min(
                    self.sessions.keys(),
                    key=lambda k: self.sessions[k].updated_at
                )
                del self.sessions[oldest_id]
                logger.warning(f"Evicted active session due to limit: {oldest_id}")

    def export_session(self, session_id: str) -> Optional[str]:
        """
        Export session as JSON.

        Args:
            session_id: Session identifier

        Returns:
            JSON string if session found
        """
        session = self.get_session(session_id)
        if session:
            return json.dumps(session.to_dict(), indent=2)
        return None

    def import_session(self, session_data: str) -> Optional[PresentationSession]:
        """
        Import session from JSON.

        Args:
            session_data: JSON string

        Returns:
            Imported session if successful
        """
        try:
            data = json.loads(session_data)

            # Convert ISO strings back to datetime
            for field in ["created_at", "updated_at", "expires_at"]:
                if data.get(field):
                    data[field] = datetime.fromisoformat(data[field])

            session = PresentationSession(**data)

            with self.lock:
                self.sessions[session.id] = session

            logger.info(f"Imported session: {session.id}")
            return session

        except Exception as e:
            logger.error(f"Failed to import session: {e}")
            return None

    def clear_all(self):
        """Clear all sessions."""
        with self.lock:
            count = len(self.sessions)
            self.sessions.clear()
            logger.info(f"Cleared {count} sessions")