import asyncio
import os
import sys
import json
from typing import Dict, List, Any
from dotenv import load_dotenv
from google.genai import types
from google.adk.runners import Runner
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService

# Add parent directory to path to import base client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_arango_client import EnhancedArangoClient, ArangoSessionService

# Import the agent
from outline import agent

load_dotenv()

class OutlineArangoClient(EnhancedArangoClient):
    """Outline-specific ArangoDB client with presentation structure management"""
    
    def __init__(self):
        super().__init__(agent_name="outline")
    
    async def store_presentation_outline(self, presentation_id: str, outline: List[str], clarified_content: str = None) -> Dict:
        """Store the presentation outline and update status"""
        # Save the outline
        outline_doc = await self.save_outline(presentation_id, outline)
        
        # Update presentation status and title (if available)
        title = outline[0] if outline else None
        await self.update_presentation_status(presentation_id, "outlined", title)
        
        # Optionally store the clarified content that led to this outline
        if clarified_content:
            await self.add_clarification(presentation_id, "clarified_summary", clarified_content)
        
        return outline_doc
    
    async def get_outline_for_generation(self, presentation_id: str) -> Dict:
        """Get outline formatted for slide generation"""
        outline_doc = await self.get_outline(presentation_id)
        if not outline_doc:
            return None
        
        # Get clarification context for enriched slide generation
        clarifications = await self.get_clarification_history(presentation_id)
        clarified_goals = ""
        
        for entry in clarifications:
            if entry["role"] == "clarified_summary":
                clarified_goals = entry["content"]
                break
        
        return {
            "outline": outline_doc["outline"],
            "clarified_goals": clarified_goals,
            "slide_count": len(outline_doc["outline"]),
            "created_at": outline_doc["created_at"]
        }
    
    async def validate_outline_structure(self, outline: List[str]) -> Dict:
        """Validate outline meets requirements (6-12 slides, proper format)"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check slide count
        if len(outline) < 6:
            validation_result["errors"].append(f"Too few slides: {len(outline)} (minimum 6)")
            validation_result["valid"] = False
        elif len(outline) > 12:
            validation_result["warnings"].append(f"Many slides: {len(outline)} (recommended max 12)")
        
        # Check title format
        for i, title in enumerate(outline, 1):
            if len(title.split()) < 3:
                validation_result["warnings"].append(f"Slide {i} title may be too short: '{title}'")
            elif len(title.split()) > 8:
                validation_result["warnings"].append(f"Slide {i} title may be too long: '{title}'")
        
        return validation_result


async def async_main():
    """Example usage of the enhanced outline client"""
    # Initialize the outline-specific client
    outline_client = OutlineArangoClient()
    await outline_client.connect()
    
    try:
        # Create session service
        session_service = ArangoSessionService(outline_client)
        
        # Use existing presentation or create new one
        presentation_id = "test_presentation_001"
        user_id = "test_user"
        
        # Ensure presentation exists
        await outline_client.create_presentation(presentation_id, user_id)
        
        # Set up the runner
        root_agent = agent.root_agent
        runner = Runner(
            app_name='outline_app',
            agent=root_agent,
            session_service=session_service,
            artifact_service=InMemoryArtifactService()
        )
        
        # Create a session
        session = await session_service.create_session(
            app_name='outline_app', 
            user_id=user_id,
            session_id=f"{presentation_id}_outline"
        )
        
        # Simulate clarified content for outline generation
        clarified_content = "Create a 20-minute technical presentation about AI for software developers, covering machine learning basics, practical applications, and implementation considerations."
        
        # Prepare input for outline agent
        outline_input = {
            "clarifiedContent": clarified_content,
            "constraints": {
                "max_slides": 10,
                "duration": 20
            }
        }
        
        print(f"\nGenerating outline for: {clarified_content}")
        
        # Run the agent
        content = types.Content(role='user', parts=[types.Part(text=json.dumps(outline_input))])
        
        print("Running outline agent...")
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
                
                # Parse outline response
                try:
                    response_data = json.loads(response_text)
                    outline = response_data.get("outline", [])
                    
                    if outline:
                        # Validate outline
                        validation = await outline_client.validate_outline_structure(outline)
                        print(f"\nOutline validation: {validation}")
                        
                        # Store outline
                        stored_outline = await outline_client.store_presentation_outline(
                            presentation_id, outline, clarified_content
                        )
                        
                        print(f"\nStored outline with {len(outline)} slides:")
                        for i, title in enumerate(outline, 1):
                            print(f"  {i}. {title}")
                        
                        # Test retrieval for generation
                        generation_data = await outline_client.get_outline_for_generation(presentation_id)
                        print(f"\nOutline ready for generation: {generation_data is not None}")
                    else:
                        print("No outline found in agent response")
                        
                except json.JSONDecodeError:
                    print(f"Agent response (not JSON): {response_text}")
                
                break
        
        # Show final presentation state
        print("\n=== Presentation State ===")
        state = await outline_client.get_presentation_state(presentation_id)
        if state:
            print(f"Status: {state['metadata']['status']}")
            print(f"Title: {state['metadata'].get('title', 'Not set')}")
            if state.get('outline'):
                print(f"Outline slides: {len(state['outline']['outline'])}")
    
    finally:
        await outline_client.close()


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")