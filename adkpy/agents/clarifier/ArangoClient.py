import asyncio
import os
import sys
import json
from typing import Dict, Any
from dotenv import load_dotenv
from google.genai import types
from google.adk.runners import Runner
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService

# Add parent directory to path to import base client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_arango_client import EnhancedArangoClient, ArangoSessionService

# Import the agent
from clarifier import agent

load_dotenv()

class ClarifierArangoClient(EnhancedArangoClient):
    """Clarifier-specific ArangoDB client with clarification history management"""
    
    def __init__(self):
        super().__init__(agent_name="clarifier")
    
    async def store_clarification_exchange(self, presentation_id: str, user_input: str, agent_response: str) -> Dict:
        """Store a complete clarification exchange (user question + agent response)"""
        # Store user input
        user_entry = await self.add_clarification(presentation_id, "user", user_input)
        
        # Store agent response
        agent_entry = await self.add_clarification(presentation_id, "assistant", agent_response)
        
        return {
            "user_entry": user_entry,
            "agent_entry": agent_entry
        }
    
    async def get_conversation_context(self, presentation_id: str) -> str:
        """Get formatted conversation context for agent processing"""
        history = await self.get_clarification_history(presentation_id)
        
        if not history:
            return ""
        
        context_lines = []
        for entry in history:
            role = "User" if entry["role"] == "user" else "Assistant"
            context_lines.append(f"{role}: {entry['content']}")
        
        return "\n".join(context_lines)
    
    async def finalize_clarification(self, presentation_id: str, final_summary: str) -> Dict:
        """Mark clarification as complete and store final summary"""
        # Store the final summary
        summary_entry = await self.add_clarification(presentation_id, "summary", final_summary)
        
        # Update presentation status
        await self.update_presentation_status(presentation_id, "clarified")
        
        return summary_entry


async def async_main():
    """Example usage of the enhanced clarifier client"""
    # Initialize the clarifier-specific client
    clarifier_client = ClarifierArangoClient()
    await clarifier_client.connect()
    
    try:
        # Create session service
        session_service = ArangoSessionService(clarifier_client)
        
        # Create a test presentation
        presentation_id = "test_presentation_001"
        user_id = "test_user"
        
        await clarifier_client.create_presentation(presentation_id, user_id)
        
        # Set up the runner
        root_agent = agent.root_agent
        runner = Runner(
            app_name='clarifier_app',
            agent=root_agent,
            session_service=session_service,
            artifact_service=InMemoryArtifactService()
        )
        
        # Create a session
        session = await session_service.create_session(
            app_name='clarifier_app', 
            user_id=user_id,
            session_id=presentation_id
        )
        
        # Simulate a clarification process
        user_query = "I need to make a presentation about AI"
        print(f"\nUser Query: '{user_query}'")
        
        # Store initial input
        await clarifier_client.add_clarification(presentation_id, "user", user_query)
        
        # Run the agent
        content = types.Content(role='user', parts=[types.Part(text=user_query)])
        
        print("Running clarifier agent...")
        events_async = runner.run_async(
            session_id=session.id, user_id=session.user_id, new_message=content
        )
        
        async for event in events_async:
            if event.is_final_response():
                # Extract agent response
                response_text = ""
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
                
                # Store agent response
                await clarifier_client.add_clarification(presentation_id, "assistant", response_text)
                
                # Parse response to check if finished
                try:
                    response_data = json.loads(response_text)
                    if response_data.get("finished", False):
                        await clarifier_client.finalize_clarification(presentation_id, response_data.get("response", ""))
                        print("Clarification process completed!")
                    else:
                        print(f"Clarification question: {response_data.get('response', '')}")
                except json.JSONDecodeError:
                    print(f"Agent response: {response_text}")
                
                break
        
        # Show final conversation history
        print("\n=== Clarification History ===")
        history = await clarifier_client.get_clarification_history(presentation_id)
        for entry in history:
            role = entry["role"].upper()
            content = entry["content"]
            timestamp = entry["timestamp"]
            print(f"[{timestamp}] {role}: {content}")
    
    finally:
        await clarifier_client.close()


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")