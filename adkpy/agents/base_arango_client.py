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
import hashlib

from dotenv import load_dotenv
from arango import ArangoClient, ArangoError
from arango.database import StandardDatabase
from arango.collection import StandardCollection
try:
    from google.adk.sessions import Session, SessionService, SessionError  # type: ignore
except Exception:
    class SessionError(Exception):
        pass

    class Session:
        def __init__(self, app_name: str, user_id: str, id: str | None = None, state: dict | None = None):
            self.app_name = app_name
            self.user_id = user_id
            self.id = id
            self.state = state or {}

        def model_dump(self):
            return {
                'app_name': self.app_name,
                'user_id': self.user_id,
                'id': self.id,
                'state': self.state,
            }

    class SessionService:  # minimal base
        pass

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
    image_url: Optional[str] = None
    use_generated_image: Optional[bool] = None
    asset_image_url: Optional[str] = None
    design_code: Optional[Dict[str, Any]] = None
    design_spec: Optional[Dict[str, Any]] = None
    constraints_override: Optional[Dict[str, Any]] = None
    use_constraints: Optional[bool] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

@dataclass
class ResearchNoteEntry:
    presentation_id: str
    note_id: str
    query: str
    rules: List[str]
    allow_domains: Optional[List[str]] = None
    top_k: Optional[int] = None
    model: Optional[str] = None
    extractions: Optional[List[str]] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if self.created_at is None:
            self.created_at = now
        self.updated_at = now


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
            'sessions': [],  # Existing collection
            'messages': ['presentation_id', 'agent'],
            'assets': ['presentation_id', 'url'],
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

    async def replace_clarifications(self, presentation_id: str, clarifications: List[Dict[str, Any]]) -> Dict:
        """Replace entire clarification history for a presentation."""
        self._ensure_simple_collection('clarifications')
        self._db.aql.execute('FOR c IN clarifications FILTER c.presentation_id == @pid REMOVE c', bind_vars={'pid': presentation_id})
        inserted = []
        for sequence, item in enumerate(clarifications or [], start=1):
            role = (item.get('role') or 'assistant').lower()
            if role not in ('user', 'assistant'):
                role = 'assistant'
            entry = ClarificationEntry(
                presentation_id=presentation_id,
                sequence=sequence,
                role=role,
                content=item.get('content', ''),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            doc = asdict(entry)
            result = self._collections['clarifications'].insert(doc, return_new=True)
            inserted.append(result.get('new', doc))
        return {'count': len(inserted)}


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

    async def replace_slides(self, presentation_id: str, slides: List[SlideContent]) -> Dict:
        """Replace all slides for a presentation with the provided set."""
        self._ensure_simple_collection('slides')
        self._db.aql.execute('FOR s IN slides FILTER s.presentation_id == @pid REMOVE s', bind_vars={'pid': presentation_id})
        inserted = []
        for raw in slides or []:
            slide = raw
            slide.presentation_id = presentation_id
            slide.version = 1
            slide.agent_source = self.agent_name
            slide.created_at = datetime.now(timezone.utc).isoformat()
            slide.updated_at = slide.created_at
            doc = asdict(slide)
            doc = {k: v for k, v in doc.items() if v is not None}
            doc['_key'] = f"{presentation_id}_{slide.slide_index}_{slide.version}"
            result = self._collections['slides'].insert(doc, return_new=True)
            inserted.append(result.get('new', doc))
        return {'count': len(inserted)}


    async def replace_research_notes(self, presentation_id: str, notes: List[Dict[str, Any]]) -> Dict:
        """Replace research notes for a presentation."""
        self._ensure_simple_collection('research_notes')
        self._db.aql.execute('FOR n IN research_notes FILTER n.presentation_id == @pid REMOVE n', bind_vars={'pid': presentation_id})
        inserted: List[Dict[str, Any]] = []
        for raw in notes or []:
            note_id = raw.get('note_id') or raw.get('id')
            if not note_id:
                note_id = self._make_research_key(presentation_id, str(len(inserted)))
            rules_value = raw.get('rules') or []
            if isinstance(rules_value, str):
                rules_list = [rules_value]
            elif isinstance(rules_value, list):
                rules_list = [str(r) for r in rules_value if r]
            else:
                rules_list = []
            allow_value = raw.get('allow_domains') or []
            if isinstance(allow_value, str):
                allow_domains = [allow_value]
            elif isinstance(allow_value, list):
                allow_domains = [str(a) for a in allow_value if a]
            else:
                allow_domains = []
            extractions_value = raw.get('extractions') or []
            if isinstance(extractions_value, str):
                extractions_list = [extractions_value]
            elif isinstance(extractions_value, list):
                extractions_list = [str(e) for e in extractions_value if e]
            else:
                extractions_list = []
            entry = ResearchNoteEntry(
                presentation_id=presentation_id,
                note_id=note_id,
                query=raw.get('query', ''),
                rules=rules_list,
                allow_domains=allow_domains if allow_domains else None,
                top_k=raw.get('top_k'),
                model=raw.get('model'),
                extractions=extractions_list if extractions_list else None,
                created_at=raw.get('created_at'),
            )
            doc = asdict(entry)
            doc['_key'] = self._make_research_key(presentation_id, note_id)
            self._collections['research_notes'].insert(doc, overwrite=True)
            inserted.append(doc)
        return {'count': len(inserted)}

    async def get_research_notes(self, presentation_id: str) -> List[Dict]:
        """Retrieve stored research notes for a presentation."""
        self._ensure_simple_collection('research_notes')
        cursor = self._db.aql.execute(
            'FOR n IN research_notes FILTER n.presentation_id == @pid SORT n.created_at RETURN n',
            bind_vars={'pid': presentation_id},
        )
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
            'research_notes': await self.get_research_notes(presentation_id),
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

    async def save_message(self, presentation_id: str, agent: str, role: str, content: str, channel: str = 'llm', meta: Optional[Dict[str, Any]] = None) -> Dict:
        """Persist a single agent message (inbound/outbound)."""
        try:
            doc = {
                'presentation_id': presentation_id,
                'agent': agent,
                'role': role,
                'channel': channel,
                'content': content,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
            if meta:
                doc['meta'] = meta
            # Ensure collection exists
            if 'messages' not in self._collections:
                self._collections['messages'] = self._db.collection('messages')
            res = self._collections['messages'].insert(doc, return_new=True)
            key = res.get('new', {}).get('_key')
            # Also record an activity edge agents -> messages (best-effort)
            try:
                if not self._db.has_collection('agents'):
                    self._db.create_collection('agents')
                agents_col = self._db.collection('agents')
                if not agents_col.get(agent):
                    agents_col.insert({'_key': agent, 'name': agent, 'created_at': datetime.now(timezone.utc).isoformat()})
                if not self._db.has_collection('activity_edges'):
                    self._db.create_collection('activity_edges', edge=True)
                self._db.collection('activity_edges').insert({
                    '_from': f'agents/{agent}',
                    '_to': f'messages/{key}',
                    'presentation_id': presentation_id,
                    'relation': 'logged',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                })
            except Exception:
                pass
            return {'ok': True, 'key': key}
        except Exception as e:
            logger.warning(f"save_message failed for {presentation_id}:{agent} - {e}")
            return {'ok': False, 'error': str(e)}

    async def list_presentations(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List presentations metadata (newest first)."""
        try:
            cursor = self._db.aql.execute(
                'FOR p IN presentations SORT p.updated_at DESC LIMIT @offset, @limit RETURN p',
                bind_vars={'limit': int(max(1, min(200, limit))), 'offset': int(max(0, offset))}
            )
            return list(cursor)
        except Exception as e:
            logger.error(f"list_presentations failed: {e}")
            return []

    async def list_messages(self, presentation_id: str, agent: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List logged messages for a presentation, newest first."""
        try:
            if agent:
                q = (
                    'FOR m IN messages FILTER m.presentation_id == @pid AND m.agent == @agent '
                    'SORT m.created_at DESC LIMIT @offset, @limit RETURN m'
                )
                bind = {'pid': presentation_id, 'agent': agent, 'limit': int(max(1, min(200, limit))), 'offset': int(max(0, offset))}
            else:
                q = (
                    'FOR m IN messages FILTER m.presentation_id == @pid '
                    'SORT m.created_at DESC LIMIT @offset, @limit RETURN m'
                )
                bind = {'pid': presentation_id, 'limit': int(max(1, min(200, limit))), 'offset': int(max(0, offset))}
            cursor = self._db.aql.execute(q, bind_vars=bind)
            return list(cursor)
        except Exception as e:
            logger.error(f"list_messages failed: {e}")
            return []

    async def register_asset(self, presentation_id: str, category: str, name: str, url: str, *, path: str | None = None, size: int | None = None, mime: str | None = None) -> dict:
        """Register or update an uploaded asset record for a presentation."""
        try:
            self._ensure_simple_collection('assets')
            col = self._collections['assets']
            now = datetime.now(timezone.utc).isoformat()
            payload = {
                'presentation_id': presentation_id,
                'category': (category or 'general').lower(),
                'name': name,
                'url': url,
                'path': path,
                'size': size,
                'mime': mime,
                'updated_at': now,
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            cursor = self._db.aql.execute(
                'FOR a IN assets FILTER a.presentation_id == @pid AND a.url == @url LIMIT 1 RETURN a',
                bind_vars={'pid': presentation_id, 'url': url},
            )
            existing = list(cursor)
            if existing:
                asset = existing[0]
                key = asset.get('_key') or (asset.get('_id', '').split('/')[-1] if asset.get('_id') else None)
                if key:
                    asset['_key'] = key
                else:
                    key = self._make_asset_key(presentation_id, url, name)
                    asset['_key'] = key
                asset.update(payload)
                asset.setdefault('created_at', now)
                col.update(asset)
                stored = col.get(asset['_key']) if asset.get('_key') else asset
                return {'ok': True, 'asset': stored}
            doc = payload
            doc['_key'] = self._make_asset_key(presentation_id, url, name)
            doc['created_at'] = now
            meta = col.insert(doc, return_new=True)
            stored = meta.get('new', doc)
            return {'ok': True, 'asset': stored}
        except Exception as e:
            logger.error(f'register_asset failed: {e}')
            return {'ok': False, 'error': str(e)}

    def _make_asset_key(self, presentation_id: str, url: str, name: str | None = None) -> str:
        base = f"{presentation_id}:{url or name or ''}"
        digest = hashlib.sha1(base.encode('utf-8', 'ignore')).hexdigest()[:16]
        prefix = ''.join(c for c in presentation_id if c.isalnum() or c in '-_') or 'asset'
        return f"{prefix}-{digest}"

    def _make_research_key(self, presentation_id: str, note_id: str | None = None) -> str:
        base = f"{presentation_id}:{note_id or ''}"
        digest = hashlib.sha1(base.encode('utf-8', 'ignore')).hexdigest()[:16]
        prefix = ''.join(c for c in presentation_id if c.isalnum() or c in '-_') or 'note'
        return f"{prefix}-research-{digest}"
    # --- Project graph helpers ---
    def _ensure_simple_collection(self, name: str):
        try:
            if name not in self._collections:
                if not self._db.has_collection(name):
                    self._db.create_collection(name)
                self._collections[name] = self._db.collection(name)
        except Exception as e:
            logger.warning(f"Failed to ensure collection {name}: {e}")

    async def upsert_presentation_metadata(self, presentation_id: str, patch: Dict[str, Any]) -> Dict:
        try:
            self._ensure_simple_collection('presentations')
            col = self._collections['presentations']
            doc = col.get({'_key': presentation_id}) or col.get(presentation_id)
            if not doc:
                doc = {'_key': presentation_id, 'presentation_id': presentation_id, 'user_id': 'default', 'created_at': datetime.now(timezone.utc).isoformat()}
            doc.update({k: v for k, v in (patch or {}).items()})
            doc['updated_at'] = datetime.now(timezone.utc).isoformat()
            if col.has(doc.get('_key')):
                col.update(doc)
            else:
                col.insert(doc)
            return {'ok': True}
        except Exception as e:
            logger.error(f"upsert_presentation_metadata failed: {e}")
            return {'ok': False, 'error': str(e)}

    async def create_project_node(self, presentation_id: str, node_type: str, data: Dict[str, Any]) -> Dict:
        try:
            self._ensure_simple_collection('project_nodes')
            col = self._collections['project_nodes']
            doc = {
                'presentation_id': presentation_id,
                'node_type': node_type,
                'data': data,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
            meta = col.insert(doc, return_new=True)
            return {'ok': True, 'node': meta.get('new')}
        except Exception as e:
            logger.error(f"create_project_node failed: {e}")
            return {'ok': False, 'error': str(e)}

    async def create_project_link(self, presentation_id: str, relation: str, from_node: Dict[str, Any], to_node: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> Dict:
        try:
            self._ensure_simple_collection('project_links')
            col = self._collections['project_links']
            doc = {
                'presentation_id': presentation_id,
                'relation': relation,
                'from': from_node.get('_id') or from_node.get('_key'),
                'to': to_node.get('_id') or to_node.get('_key'),
                'meta': meta or {},
                'created_at': datetime.now(timezone.utc).isoformat(),
            }
            col.insert(doc)
            return {'ok': True}
        except Exception as e:
            logger.error(f"create_project_link failed: {e}")
            return {'ok': False, 'error': str(e)}

    async def get_reviews(self, presentation_id: str, slide_index: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        """List saved critic reviews for a slide (newest first). Supports offset for pagination."""
        try:
            cursor = self._db.aql.execute(
                'FOR r IN reviews FILTER r.presentation_id == @pid AND r.slide_index == @idx '
                'SORT r.created_at DESC LIMIT @offset, @limit RETURN r',
                bind_vars={'pid': presentation_id, 'idx': int(slide_index), 'limit': int(max(1, min(limit, 50))), 'offset': int(max(0, offset))}
            )
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to fetch reviews for {presentation_id}:{slide_index} - {e}")
            return []


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