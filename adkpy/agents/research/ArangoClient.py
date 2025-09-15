import asyncio
import os
from dotenv import load_dotenv
from arango import ArangoClient
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import Session, SessionService, SessionError
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService

# Assuming your clarifier agent is structured similarly to the planner
from clarifier import agent

# --- Environment Setup ---
# Create a .env file in the same directory with these variables
# ARANGODB_URL="http://arangodb:8529"
# ARANGODB_USER="root"
# ARANGODB_PASSWORD="root"
# ARANGODB_DB="presentpro"
load_dotenv()

class ArangoSessionService(SessionService):
    """A session service that stores session data in ArangoDB."""

    def __init__(self, db):
        self._db = db
        if not self._db.has_collection('sessions'):
            self._sessions_collection = self._db.create_collection('sessions')
        else:
            self._sessions_collection = self._db.collection('sessions')

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
            id=session_id,  # Arango will generate a _key if this is None
            state=state or {},
        )
        
        # The document key in ArangoDB will be the session ID
        doc = new_session.model_dump()
        if session_id:
            doc['_key'] = session_id
            
        meta = self._sessions_collection.insert(doc, return_new=True)
        
        # Update the session object with the key assigned by ArangoDB
        new_session.id = meta['new']['_key']
        
        print(f"Created session {new_session.id} in ArangoDB.")
        return new_session

    async def get_session(
        self, app_name: str, user_id: str, session_id: str
    ) -> Session | None:
        """Retrieves a session from ArangoDB."""
        doc = self._sessions_collection.get(session_id)
        if doc:
            # Ensure the retrieved session matches the app and user context
            if doc.get('app_name') == app_name and doc.get('user_id') == user_id:
                print(f"Retrieved session {session_id} from ArangoDB.")
                # The 'id' field in the ADK Session corresponds to Arango's '_key'
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
        print(f"Updated session {session.id} in ArangoDB.")


async def async_main():
    # 1. Initialize ArangoDB connection
    arango_host = os.getenv("ARANGODB_URL", "http://arangodb:8529")
    arango_user = os.getenv("ARANGODB_USER", "root")
    arango_password = os.getenv("ARANGODB_PASSWORD") or os.getenv("ARANGO_ROOT_PASSWORD")
    db_name = os.getenv("ARANGODB_DB", "presentpro")

    if not arango_password:
        raise ValueError("ARANGODB_PASSWORD (or ARANGO_ROOT_PASSWORD fallback) environment variable is not set.")

    try:
        client = ArangoClient(hosts=arango_host)
        sys_db = client.db("_system", username=arango_user, password=arango_password)
        
        if not sys_db.has_database(db_name):
            sys_db.create_database(db_name)
            print(f"Created ArangoDB database: '{db_name}'")

        db = client.db(db_name, username=arango_user, password=arango_password)
    except Exception as e:
        print(f"Failed to connect to ArangoDB: {e}")
        return

    # 2. Instantiate the custom ArangoSessionService
    session_service = ArangoSessionService(db)

    # 3. Create a session for the agent to use
    session = await session_service.create_session(
        app_name='clarifier_app', user_id='user_arango_client'
    )

    # 4. Set up the runner
    root_agent = agent.root_agent
    runner = Runner(
        app_name='clarifier_app',
        agent=root_agent,
        session_service=session_service,
        artifact_service=InMemoryArtifactService() # Using in-memory for artifacts for simplicity
    )

    # 5. Run the agent with a user query
    query = "I need to make a presentation about AI"
    print(f"\nUser Query: '{query}'")
    content = types.Content(role='user', parts=[types.Part(text=query)])

    print("Running agent...")
    events_async = runner.run_async(
        session_id=session.id, user_id=session.user_id, new_message=content
    )

    async for event in events_async:
        print(f"Event received: {event}")


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")