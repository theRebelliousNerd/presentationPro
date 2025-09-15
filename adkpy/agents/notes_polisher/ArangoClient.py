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
from notes_polisher import agent

load_dotenv()

class NotesPolisherArangoClient(EnhancedArangoClient):
    """Notes Polisher-specific ArangoDB client with enhanced speaker notes management"""
    
    def __init__(self):
        super().__init__(agent_name="notes_polisher")
    
    async def store_enhanced_notes(self, presentation_id: str, slide_index: int, original_notes: str, enhanced_notes: str, tone: str = "professional") -> Dict:
        """Store enhanced speaker notes with original for comparison"""
        # Store enhanced notes
        stored_notes = await self.save_enhanced_notes(presentation_id, slide_index, enhanced_notes)
        
        # Store enhancement metadata for tracking
        enhancement_metadata = {
            "presentation_id": presentation_id,
            "slide_index": slide_index,
            "original_notes": original_notes,
            "enhanced_notes": enhanced_notes,
            "tone": tone,
            "agent_source": self.agent_name,
            "created_at": stored_notes["created_at"]
        }
        
        return stored_notes
    
    async def get_slides_for_enhancement(self, presentation_id: str) -> List[Dict]:
        """Get all slides that need speaker notes enhancement"""
        slides = await self.get_latest_slides(presentation_id)
        
        # Format for notes enhancement
        slides_needing_enhancement = []
        for slide in slides:
            if slide.get("speaker_notes"):  # Only process slides with existing notes
                slides_needing_enhancement.append({
                    "slide_index": slide["slide_index"],
                    "title": slide["title"],
                    "content": slide["content"],
                    "speaker_notes": slide["speaker_notes"],
                    "version": slide["version"]
                })
        
        return sorted(slides_needing_enhancement, key=lambda x: x["slide_index"])
    
    async def batch_enhance_notes(self, presentation_id: str, tone: str = "professional") -> Dict:
        """Enhance notes for all slides in the presentation"""
        slides = await self.get_slides_for_enhancement(presentation_id)
        enhanced_count = 0
        
        session_service = ArangoSessionService(self)
        root_agent = agent.root_agent
        runner = Runner(
            app_name='notes_polisher_app',
            agent=root_agent,
            session_service=session_service,
            artifact_service=InMemoryArtifactService()
        )
        
        for slide in slides:
            try:
                # Create session for this enhancement
                session = await session_service.create_session(
                    app_name='notes_polisher_app',
                    user_id='system',
                    session_id=f"{presentation_id}_notes_{slide['slide_index']}"
                )
                
                # Prepare enhancement input
                enhancement_input = {
                    "speakerNotes": slide["speaker_notes"],
                    "tone": tone
                }
                
                # Run the agent
                content = types.Content(role='user', parts=[types.Part(text=json.dumps(enhancement_input))])
                events_async = runner.run_async(
                    session_id=session.id, user_id='system', new_message=content
                )
                
                async for event in events_async:
                    if event.is_final_response():
                        response_text = ""
                        for part in event.content.parts:
                            if part.text:
                                response_text += part.text
                        
                        try:
                            response_data = json.loads(response_text)
                            enhanced_notes = response_data.get("rephrasedSpeakerNotes", "")
                            
                            if enhanced_notes:
                                await self.store_enhanced_notes(
                                    presentation_id, 
                                    slide["slide_index"], 
                                    slide["speaker_notes"], 
                                    enhanced_notes, 
                                    tone
                                )
                                enhanced_count += 1
                        except json.JSONDecodeError:
                            print(f"Failed to parse enhancement for slide {slide['slide_index']}")
                        break
                        
            except Exception as e:
                print(f"Error enhancing notes for slide {slide['slide_index']}: {e}")
        
        # Update presentation status
        if enhanced_count > 0:
            await self.update_presentation_status(presentation_id, "notes_enhanced")
        
        return {
            "enhanced_count": enhanced_count,
            "total_slides": len(slides),
            "success_rate": enhanced_count / len(slides) if slides else 0
        }


async def async_main():
    """Example usage of the notes polisher client"""
    notes_client = NotesPolisherArangoClient()
    await notes_client.connect()
    
    try:
        presentation_id = "test_presentation_001"
        
        # Get slides that need enhancement
        slides = await notes_client.get_slides_for_enhancement(presentation_id)
        print(f"Found {len(slides)} slides with speaker notes to enhance")
        
        if slides:
            # Enhance all notes with professional tone
            result = await notes_client.batch_enhance_notes(presentation_id, "professional")
            print(f"Enhanced {result['enhanced_count']} out of {result['total_slides']} slides")
            print(f"Success rate: {result['success_rate']:.2%}")
        
    finally:
        await notes_client.close()


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")