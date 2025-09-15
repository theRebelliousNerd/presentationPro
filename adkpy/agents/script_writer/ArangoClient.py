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
from script_writer import agent

load_dotenv()

class ScriptWriterArangoClient(EnhancedArangoClient):
    """Script Writer-specific ArangoDB client with presentation script management"""
    
    def __init__(self):
        super().__init__(agent_name="script_writer")
    
    async def generate_presentation_script(self, presentation_id: str, include_assets: bool = True) -> Dict:
        """Generate a complete presentation script from all slides"""
        # Get all slides and enhanced notes
        slides = await self.get_latest_slides(presentation_id)
        
        # Get enhanced notes if available
        enhanced_notes = {}
        cursor = self._db.aql.execute('''
            FOR n IN speaker_notes 
            FILTER n.presentation_id == @pid 
            RETURN n
        ''', bind_vars={'pid': presentation_id})
        
        for note in cursor:
            enhanced_notes[note["slide_index"]] = note["enhanced_notes"]
        
        # Prepare script generation input
        script_slides = []
        for slide in sorted(slides, key=lambda x: x["slide_index"]):
            slide_data = {
                "title": slide["title"],
                "content": slide["content"],
                "speakerNotes": enhanced_notes.get(slide["slide_index"], slide["speaker_notes"])
            }
            script_slides.append(slide_data)
        
        # Get assets for bibliography (placeholder for now)
        assets = []  # This would come from the assets system
        
        # Set up the agent
        session_service = ArangoSessionService(self)
        root_agent = agent.root_agent
        runner = Runner(
            app_name='script_writer_app',
            agent=root_agent,
            session_service=session_service,
            artifact_service=InMemoryArtifactService()
        )
        
        # Create session
        session = await session_service.create_session(
            app_name='script_writer_app',
            user_id='system',
            session_id=f"{presentation_id}_script"
        )
        
        # Prepare script input
        script_input = {
            "slides": script_slides,
            "assets": assets
        }
        
        try:
            # Run the agent
            content = types.Content(role='user', parts=[types.Part(text=json.dumps(script_input))])
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
                        script_response = json.loads(response_text)
                        script_content = script_response.get("script", "")
                        
                        if script_content:
                            # Store the complete script
                            stored_script = await self.save_script(presentation_id, script_content)
                            
                            # Update presentation status
                            await self.update_presentation_status(presentation_id, "script_generated")
                            
                            return {
                                "success": True,
                                "script_length": len(script_content),
                                "slides_processed": len(script_slides),
                                "stored_script": stored_script
                            }
                    except json.JSONDecodeError:
                        print("Failed to parse script response")
                    break
        
        except Exception as e:
            print(f"Error generating script: {e}")
        
        return {
            "success": False,
            "error": "Script generation failed"
        }
    
    async def get_presentation_script(self, presentation_id: str) -> Dict:
        """Get the stored presentation script"""
        return self._collections['scripts'].get(presentation_id)
    
    async def update_script_section(self, presentation_id: str, section_start: str, new_content: str) -> Dict:
        """Update a specific section of the script"""
        script_doc = await self.get_presentation_script(presentation_id)
        if not script_doc:
            raise ValueError("No script found for presentation")
        
        current_script = script_doc["script_content"]
        
        # Simple section replacement (could be enhanced with more sophisticated parsing)
        if section_start in current_script:
            # Find the section and replace it
            # This is a simplified implementation
            updated_script = current_script.replace(section_start, new_content)
            
            # Store updated script
            return await self.save_script(presentation_id, updated_script)
        else:
            raise ValueError(f"Section '{section_start}' not found in script")
    
    async def analyze_script_metrics(self, presentation_id: str) -> Dict:
        """Analyze script metrics like word count, estimated duration, etc."""
        script_doc = await self.get_presentation_script(presentation_id)
        if not script_doc:
            return {"error": "No script found"}
        
        script_content = script_doc["script_content"]
        
        # Basic metrics
        word_count = len(script_content.split())
        estimated_duration_minutes = word_count / 150  # Assuming 150 words per minute
        
        # Count slides referenced
        slide_references = script_content.count("[ref:")
        
        return {
            "word_count": word_count,
            "estimated_duration_minutes": round(estimated_duration_minutes, 1),
            "character_count": len(script_content),
            "slide_references": slide_references,
            "created_at": script_doc["created_at"]
        }


async def async_main():
    """Example usage of the script writer client"""
    script_client = ScriptWriterArangoClient()
    await script_client.connect()
    
    try:
        presentation_id = "test_presentation_001"
        
        # Generate presentation script
        result = await script_client.generate_presentation_script(presentation_id)
        
        if result["success"]:
            print(f"Generated script with {result['script_length']} characters")
            print(f"Processed {result['slides_processed']} slides")
            
            # Analyze script metrics
            metrics = await script_client.analyze_script_metrics(presentation_id)
            print(f"Script metrics:")
            print(f"  Word count: {metrics['word_count']}")
            print(f"  Estimated duration: {metrics['estimated_duration_minutes']} minutes")
            print(f"  Slide references: {metrics['slide_references']}")
        else:
            print(f"Script generation failed: {result.get('error', 'Unknown error')}")
        
    finally:
        await script_client.close()


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")