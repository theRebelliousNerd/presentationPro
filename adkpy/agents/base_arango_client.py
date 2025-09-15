"""
Enhanced ArangoDB client for ADK agents with multi-agent write coordination.

Database Schema Design:
- presentations: Core presentation metadata and state
- clarifications: Q&A history and clarified goals
- outlines: Presentation structure and slide titles
- slides: Individual slide content with versioning
- design_specs: Visual design specifications
- speaker_notes: Enhanced notes from notes_polisher
- scripts: Complete presentation scripts
- reviews: Critic feedback and corrections
- sessions: ADK session management (existing)

Key Design Principles:
1. presentation_id as partition key to avoid conflicts
2. Agent-specific collections with versioning
3. Timestamps for audit trails
4. Connection pooling for performance
5. Atomic operations where needed
"""

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import logging
from functools import wraps

from dotenv import load_dotenv
from arango import ArangoClient, ArangoError
from arango.database import StandardDatabase
from arango.collection import StandardCollection
from google.adk.sessions import Session, SessionService, SessionError

# Enhanced error handling and connection pooling
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ImportError:
    # Fallback retry decorator
    def retry(*args, **kwargs):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                for attempt in range(3):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt == 2:
                            raise
                        await asyncio.sleep(2 ** attempt)
            return wrapper
        return decorator
    
    stop_after_attempt = lambda x: None
    wait_exponential = lambda **kwargs: None
    retry_if_exception_type = lambda x: None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

@dataclass
class PresentationMetadata:
    """Core presentation metadata"""
    presentation_id: str
    user_id: str
    title: Optional[str] = None
    status: str = "initial"  # initial, clarifying, outlined, generating, completed
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

@dataclass
class ClarificationEntry:
    """Single clarification exchange"""
    presentation_id: str
    sequence: int
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

@dataclass
class SlideContent:
    """Individual slide content with versioning"""
    presentation_id: str
    slide_index: int
    title: str
    content: List[str]
    speaker_notes: str
    image_prompt: str
    version: int = 1
    agent_source: str = "slide_writer"  # Which agent created/modified
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

class ConnectionPool:
    """Simple connection pool for ArangoDB clients"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._pool = asyncio.Queue(maxsize=max_connections)
        self._created_connections = 0
        self._lock = asyncio.Lock()
    
    async def get_connection(self, host: str, user: str, password: str, db_name: str):
        """Get a connection from the pool or create a new one"""
        try:
            # Try to get an existing connection
            connection_info = self._pool.get_nowait()
            return connection_info
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            async with self._lock:
                if self._created_connections < self.max_connections:
                    client = ArangoClient(hosts=host)
                    db = client.db(db_name, username=user, password=password)
                    self._created_connections += 1
                    return {'client': client, 'db': db}
                else:
                    # Wait for an available connection
                    return await self._pool.get()
    
    async def return_connection(self, connection_info: Dict):
        """Return a connection to the pool"""
        try:
            self._pool.put_nowait(connection_info)
        except asyncio.QueueFull:
            # Pool is full, close the connection
            connection_info['client'].close()


class EnhancedArangoClient:
    """Enhanced ArangoDB client with connection pooling and multi-agent coordination"""
    
    _connection_pool = None
    _pool_lock = asyncio.Lock()
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._client = None
        self._db = None
        self._collections = {}
        self._connection_info = None
        
        # Connection parameters
        self.arango_host = os.getenv("ARANGODB_URL", "http://arangodb:8529")
        self.arango_user = os.getenv("ARANGODB_USER", "root")
        self.arango_password = os.getenv("ARANGODB_PASSWORD") or os.getenv("ARANGO_ROOT_PASSWORD", "root")
        self.db_name = os.getenv("ARANGODB_DB", "presentpro")
        
        # Initialize class-level connection pool
        if EnhancedArangoClient._connection_pool is None:
            EnhancedArangoClient._connection_pool = ConnectionPool()
        
        logger.info(f"Initialized ArangoClient for agent: {agent_name}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def connect(self):
        """Establish connection to ArangoDB with retry logic and connection pooling"""
        try:
            # Get connection from pool
            self._connection_info = await self._connection_pool.get_connection(
                self.arango_host, self.arango_user, self.arango_password, self.db_name
            )
            
            self._client = self._connection_info['client']
            self._db = self._connection_info['db']
            
            # Ensure database exists (only check, don't create multiple times)
            try:
                # Test connection
                self._db.properties()
            except ArangoError:
                # Database might not exist, create it
                sys_db = self._client.db("_system", username=self.arango_user, password=self.arango_password)
                if not sys_db.has_database(self.db_name):
                    sys_db.create_database(self.db_name)
                    logger.info(f"Created ArangoDB database: '{self.db_name}'")
                
                # Reconnect to the new database
                self._db = self._client.db(self.db_name, username=self.arango_user, password=self.arango_password)
            
            # Initialize collections
            await self._initialize_collections()
            
            logger.info(f"Connected to ArangoDB successfully (agent: {self.agent_name})")
            
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            raise ConnectionError(f"Failed to connect to ArangoDB: {e}")
    
    async def _initialize_collections(self):
        """Initialize all required collections with proper indexes"""
        collections_config = {
            'presentations': ['presentation_id', 'user_id'],
            'clarifications': ['presentation_id', 'sequence'],
            'outlines': ['presentation_id'],
            'slides': ['presentation_id', 'slide_index'],
            'design_specs': ['presentation_id'],
            'speaker_notes': ['presentation_id', 'slide_index'],
            'scripts': ['presentation_id'],
            'reviews': ['presentation_id', 'agent_source'],
            'sessions': []  # Existing collection
        }
        
        for collection_name, indexes in collections_config.items():
            # Create collection if it doesn't exist
            if not self._db.has_collection(collection_name):
                collection = self._db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            else:
                collection = self._db.collection(collection_name)
            
            # Create indexes for performance
            for index_field in indexes:
                try:
                    collection.add_hash_index(fields=[index_field], unique=False)
                except ArangoError:
                    # Index might already exist
                    pass
            
            self._collections[collection_name] = collection
    
    @asynccontextmanager
    async def transaction(self, write_collections: List[str] = None, read_collections: List[str] = None):
        """Context manager for database transactions"""
        try:
            # For now, we'll use simple operations
            # ArangoDB transactions can be added later if needed
            yield self._db
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            raise
    
    # Core presentation operations with error handling
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def create_presentation(self, presentation_id: str, user_id: str) -> Dict:
        """Create a new presentation record with retry logic"""
        metadata = PresentationMetadata(presentation_id=presentation_id, user_id=user_id)
        doc = asdict(metadata)
        doc['_key'] = presentation_id
        
        try:
            result = self._collections['presentations'].insert(doc, return_new=True)
            logger.info(f"Created presentation {presentation_id} by {self.agent_name}")
            return result['new']
        except ArangoError as e:
            if "unique constraint violated" in str(e) or "duplicate" in str(e).lower():
                # Presentation already exists, return it
                existing = self._collections['presentations'].get(presentation_id)
                if existing:
                    logger.info(f"Presentation {presentation_id} already exists, returning existing")
                    return existing
            logger.error(f"Failed to create presentation {presentation_id}: {e}")
            raise
    
    async def update_presentation_status(self, presentation_id: str, status: str, title: str = None) -> Dict:
        """Update presentation status and optional title"""
        update_doc = {
            'status': status,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'last_agent': self.agent_name
        }
        
        if title:
            update_doc['title'] = title
        
        try:
            result = self._collections['presentations'].update(presentation_id, update_doc, return_new=True)
            logger.info(f"Updated presentation {presentation_id} status to {status} by {self.agent_name}")
            return result['new']
        except ArangoError as e:
            logger.error(f"Failed to update presentation {presentation_id}: {e}")
            raise
    
    # Clarifier operations
    async def add_clarification(self, presentation_id: str, role: str, content: str) -> Dict:
        """Add a clarification exchange"""
        # Get next sequence number
        cursor = self._db.aql.execute(
            'FOR c IN clarifications FILTER c.presentation_id == @pid SORT c.sequence DESC LIMIT 1 RETURN c.sequence',
            bind_vars={'pid': presentation_id}
        )
        last_sequence = list(cursor)
        next_sequence = (last_sequence[0] if last_sequence else 0) + 1
        
        clarification = ClarificationEntry(
            presentation_id=presentation_id,
            sequence=next_sequence,
            role=role,
            content=content
        )
        
        doc = asdict(clarification)
        result = self._collections['clarifications'].insert(doc, return_new=True)
        logger.info(f"Added clarification {next_sequence} for {presentation_id} by {self.agent_name}")
        return result['new']
    
    async def get_clarification_history(self, presentation_id: str) -> List[Dict]:
        """Get all clarifications for a presentation"""
        cursor = self._db.aql.execute(
            'FOR c IN clarifications FILTER c.presentation_id == @pid SORT c.sequence RETURN c',
            bind_vars={'pid': presentation_id}
        )
        return list(cursor)
    
    # Outline operations
    async def save_outline(self, presentation_id: str, outline: List[str]) -> Dict:
        """Save presentation outline"""
        doc = {
            '_key': presentation_id,
            'presentation_id': presentation_id,
            'outline': outline,
            'agent_source': self.agent_name,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            result = self._collections['outlines'].insert(doc, overwrite=True, return_new=True)
            logger.info(f"Saved outline for {presentation_id} by {self.agent_name}")
            return result['new']
        except ArangoError as e:
            logger.error(f"Failed to save outline for {presentation_id}: {e}")
            raise
    
    async def get_outline(self, presentation_id: str) -> Optional[Dict]:
        """Get presentation outline"""
        return self._collections['outlines'].get(presentation_id)
    
    # Slide operations
    async def save_slide(self, slide_content: SlideContent) -> Dict:
        """Save individual slide content with versioning"""
        # Check for existing slide to determine version
        existing_cursor = self._db.aql.execute(
            'FOR s IN slides FILTER s.presentation_id == @pid AND s.slide_index == @idx '
            'SORT s.version DESC LIMIT 1 RETURN s.version',
            bind_vars={'pid': slide_content.presentation_id, 'idx': slide_content.slide_index}
        )
        existing_versions = list(existing_cursor)
        next_version = (existing_versions[0] if existing_versions else 0) + 1
        
        slide_content.version = next_version
        slide_content.agent_source = self.agent_name
        
        doc = asdict(slide_content)
        doc['_key'] = f"{slide_content.presentation_id}_{slide_content.slide_index}_{next_version}"
        
        result = self._collections['slides'].insert(doc, return_new=True)
        logger.info(f"Saved slide {slide_content.slide_index}v{next_version} for {slide_content.presentation_id} by {self.agent_name}")
        return result['new']
    
    async def get_latest_slides(self, presentation_id: str) -> List[Dict]:
        """Get latest version of all slides for a presentation"""
        cursor = self._db.aql.execute('''
            FOR s IN slides 
            FILTER s.presentation_id == @pid 
            COLLECT slide_index = s.slide_index INTO groups
            LET latest = (FOR g IN groups SORT g.s.version DESC LIMIT 1 RETURN g.s)[0]
            SORT slide_index
            RETURN latest
        ''', bind_vars={'pid': presentation_id})
        return list(cursor)
    
    # Design operations
    async def save_design_spec(self, presentation_id: str, design_data: Dict) -> Dict:
        """Save design specifications"""
        doc = {
            '_key': presentation_id,
            'presentation_id': presentation_id,
            'design_data': design_data,
            'agent_source': self.agent_name,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self._collections['design_specs'].insert(doc, overwrite=True, return_new=True)
        logger.info(f"Saved design spec for {presentation_id} by {self.agent_name}")
        return result['new']
    
    # Notes polisher operations
    async def save_enhanced_notes(self, presentation_id: str, slide_index: int, enhanced_notes: str) -> Dict:
        """Save enhanced speaker notes"""
        doc = {
            '_key': f"{presentation_id}_{slide_index}",
            'presentation_id': presentation_id,
            'slide_index': slide_index,
            'enhanced_notes': enhanced_notes,
            'agent_source': self.agent_name,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self._collections['speaker_notes'].insert(doc, overwrite=True, return_new=True)
        logger.info(f"Saved enhanced notes for {presentation_id} slide {slide_index} by {self.agent_name}")
        return result['new']
    
    # Script writer operations
    async def save_script(self, presentation_id: str, script_content: str) -> Dict:
        """Save complete presentation script"""
        doc = {
            '_key': presentation_id,
            'presentation_id': presentation_id,
            'script_content': script_content,
            'agent_source': self.agent_name,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self._collections['scripts'].insert(doc, overwrite=True, return_new=True)
        logger.info(f"Saved script for {presentation_id} by {self.agent_name}")
        return result['new']
    
    # Critic operations
    async def save_review(self, presentation_id: str, slide_index: int, review_data: Dict) -> Dict:
        """Save critic review and corrections"""
        doc = {
            '_key': f"{presentation_id}_{slide_index}_{self.agent_name}",
            'presentation_id': presentation_id,
            'slide_index': slide_index,
            'review_data': review_data,
            'agent_source': self.agent_name,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result = self._collections['reviews'].insert(doc, overwrite=True, return_new=True)
        logger.info(f"Saved review for {presentation_id} slide {slide_index} by {self.agent_name}")
        return result['new']
    
    # Utility operations
    async def get_presentation_state(self, presentation_id: str) -> Dict:
        """Get comprehensive presentation state across all agents"""
        presentation = self._collections['presentations'].get(presentation_id)
        if not presentation:
            return None
        
        # Get all related data
        state = {
            'metadata': presentation,
            'clarifications': await self.get_clarification_history(presentation_id),
            'outline': await self.get_outline(presentation_id),
            'slides': await self.get_latest_slides(presentation_id),
        }
        
        # Get latest design spec
        design_spec = self._collections['design_specs'].get(presentation_id)
        if design_spec:
            state['design_spec'] = design_spec
        
        # Get script
        script = self._collections['scripts'].get(presentation_id)
        if script:
            state['script'] = script
        
        return state
    
    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def cleanup_old_versions(self, presentation_id: str, keep_versions: int = 5):
        """Clean up old slide versions to prevent bloat"""
        try:
            cursor = self._db.aql.execute('''
                FOR s IN slides 
                FILTER s.presentation_id == @pid 
                COLLECT slide_index = s.slide_index INTO groups
                FOR g IN groups
                    LET sorted = (FOR slide IN g SORT slide.s.version DESC RETURN slide.s)
                    LET to_delete = SLICE(sorted, @keep, LENGTH(sorted))
                    FOR old_slide IN to_delete
                        REMOVE old_slide._key IN slides
            ''', bind_vars={'pid': presentation_id, 'keep': keep_versions})
            
            logger.info(f"Cleaned up old versions for {presentation_id}, kept {keep_versions} versions")
        except ArangoError as e:
            logger.warning(f"Failed to cleanup old versions for {presentation_id}: {e}")
            # Don't raise - cleanup is not critical
    
    async def health_check(self) -> Dict:
        """Check the health of the database connection"""
        try:
            # Simple query to test connection
            cursor = self._db.aql.execute('RETURN 1')
            result = list(cursor)
            
            return {
                "healthy": True,
                "agent": self.agent_name,
                "database": self.db_name,
                "collections": len(self._collections),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed for {self.agent_name}: {e}")
            return {
                "healthy": False,
                "agent": self.agent_name,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def close(self):
        """Return connection to pool or close if pool is full"""
        if self._connection_info:
            await self._connection_pool.return_connection(self._connection_info)
            self._connection_info = None
            self._client = None
            self._db = None
            logger.info(f"Returned ArangoDB connection to pool for agent: {self.agent_name}")


class ArangoSessionService(SessionService):
    """Enhanced session service that integrates with the unified schema"""
    
    def __init__(self, arango_client: EnhancedArangoClient):
        self.arango_client = arango_client
        self._sessions_collection = arango_client._collections['sessions']
    
    async def create_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str | None = None,
        state: dict | None = None,
    ) -> Session:
        """Creates a new session in ArangoDB."""
        if session_id and self._sessions_collection.has(session_id):
            raise SessionError(f'Session with ID {session_id} already exists')

        new_session = Session(
            app_name=app_name,
            user_id=user_id,
            id=session_id,
            state=state or {},
        )
        
        doc = new_session.model_dump()
        if session_id:
            doc['_key'] = session_id
            
        meta = self._sessions_collection.insert(doc, return_new=True)
        new_session.id = meta['new']['_key']
        
        logger.info(f"Created session {new_session.id} in ArangoDB.")
        return new_session

    async def get_session(
        self, app_name: str, user_id: str, session_id: str
    ) -> Session | None:
        """Retrieves a session from ArangoDB."""
        doc = self._sessions_collection.get(session_id)
        if doc:
            if doc.get('app_name') == app_name and doc.get('user_id') == user_id:
                logger.info(f"Retrieved session {session_id} from ArangoDB.")
                doc['id'] = doc['_key']
                return Session(**doc)
        return None

    async def update_session(self, session: Session) -> None:
        """Updates an existing session in ArangoDB."""
        if not session.id:
            raise SessionError('Session ID is required for updates')
            
        doc = session.model_dump()
        doc['_key'] = session.id
        
        self._sessions_collection.update(doc)
        logger.info(f"Updated session {session.id} in ArangoDB.")
    
    async def close(self):
        """Close the session service connection"""
        if hasattr(self.arango_client, 'close'):
            await self.arango_client.close()