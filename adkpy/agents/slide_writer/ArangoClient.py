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
from base_arango_client import EnhancedArangoClient, ArangoSessionService, SlideContent

# Import the agent
from slide_writer import agent

load_dotenv()

class SlideWriterArangoClient(EnhancedArangoClient):
    """Slide Writer-specific ArangoDB client with slide content management"""
    
    def __init__(self):
        super().__init__(agent_name="slide_writer")
    
    async def store_slide_content(self, presentation_id: str, slide_index: int, slide_data: Dict) -> Dict:
        """Store individual slide content with proper structure"""
        # Create SlideContent object
        slide_content = SlideContent(
            presentation_id=presentation_id,
            slide_index=slide_index,
            title=slide_data.get("title", ""),
            content=slide_data.get("content", []),
            speaker_notes=slide_data.get("speakerNotes", ""),
            image_prompt=slide_data.get("imagePrompt", "")
        )
        
        # Save slide with versioning
        saved_slide = await self.save_slide(slide_content)
        
        # Update presentation status if this is the first slide
        if slide_index == 0:
            await self.update_presentation_status(presentation_id, "generating")
        
        return saved_slide
    
    async def get_slides_for_processing(self, presentation_id: str) -> List[Dict]:
        """Get all current slides formatted for further processing"""
        slides = await self.get_latest_slides(presentation_id)
        
        # Format for downstream agents
        formatted_slides = []
        for slide in slides:
            formatted_slides.append({
                "slide_index": slide["slide_index"],
                "title": slide["title"],
                "content": slide["content"],
                "speakerNotes": slide["speaker_notes"],
                "imagePrompt": slide["image_prompt"],
                "version": slide["version"],
                "created_at": slide["created_at"]
            })
        
        return sorted(formatted_slides, key=lambda x: x["slide_index"])
    
    async def batch_store_slides(self, presentation_id: str, slides_data: List[Dict]) -> Dict:
        """Store multiple slides efficiently"""
        stored_slides = []
        
        for i, slide_data in enumerate(slides_data):
            try:
                saved_slide = await self.store_slide_content(presentation_id, i, slide_data)
                stored_slides.append(saved_slide)
            except Exception as e:
                print(f"Error storing slide {i}: {e}")
                # Continue with other slides
        
        # Update overall status
        if stored_slides:
            await self.update_presentation_status(presentation_id, "slides_generated")
        
        return {
            "stored_count": len(stored_slides),
            "total_requested": len(slides_data),
            "success_rate": len(stored_slides) / len(slides_data) if slides_data else 0,
            "slides": stored_slides
        }
    
    async def get_outline_context(self, presentation_id: str) -> Dict:
        """Get outline and clarification context for slide generation"""
        # Get outline
        outline_doc = await self.get_outline(presentation_id)
        if not outline_doc:
            return None
        
        # Get clarifications for context
        clarifications = await self.get_clarification_history(presentation_id)
        clarified_goals = ""
        
        for entry in clarifications:
            if entry["role"] == "clarified_summary":
                clarified_goals = entry["content"]
                break
        
        return {
            "outline": outline_doc["outline"],
            "clarified_goals": clarified_goals,
            "total_slides": len(outline_doc["outline"])
        }
    
    async def validate_slide_content(self, slide_data: Dict) -> Dict:
        """Validate slide content meets quality standards"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        required_fields = ["title", "content", "speakerNotes", "imagePrompt"]
        for field in required_fields:
            if not slide_data.get(field):
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False
        
        # Check content structure
        content = slide_data.get("content", [])
        if not isinstance(content, list):
            validation_result["errors"].append("Content must be a list of bullet points")
            validation_result["valid"] = False
        elif len(content) < 2:
            validation_result["warnings"].append(f"Few bullet points: {len(content)} (recommended 2-4)")
        elif len(content) > 4:
            validation_result["warnings"].append(f"Many bullet points: {len(content)} (recommended 2-4)")
        
        # Check bullet point length
        for i, bullet in enumerate(content):
            if len(bullet.split()) > 12:
                validation_result["warnings"].append(f"Bullet {i+1} may be too long: {len(bullet.split())} words")
        
        # Check title length
        title = slide_data.get("title", "")
        if len(title.split()) > 8:
            validation_result["warnings"].append(f"Title may be too long: {len(title.split())} words")
        
        return validation_result


async def async_main():
    """Example usage of the enhanced slide writer client"""
    # Initialize the slide writer-specific client
    slide_writer_client = SlideWriterArangoClient()
    await slide_writer_client.connect()
    
    try:
        # Create session service
        session_service = ArangoSessionService(slide_writer_client)
        
        # Use existing presentation or create new one
        presentation_id = "test_presentation_001"
        user_id = "test_user"
        
        # Ensure presentation exists
        await slide_writer_client.create_presentation(presentation_id, user_id)
        
        # Set up the runner
        root_agent = agent.root_agent
        runner = Runner(
            app_name='slide_writer_app',
            agent=root_agent,
            session_service=session_service,
            artifact_service=InMemoryArtifactService()
        )
        
        # Get outline context for slide generation
        outline_context = await slide_writer_client.get_outline_context(presentation_id)
        if not outline_context:
            print("No outline found. Creating sample outline...")
            # Create a sample outline for testing
            sample_outline = [
                "Introduction to AI",
                "Machine Learning Basics",
                "Practical Applications",
                "Implementation Considerations",
                "Conclusion and Next Steps"
            ]
            await slide_writer_client.save_outline(presentation_id, sample_outline)
            outline_context = await slide_writer_client.get_outline_context(presentation_id)
        
        print(f"Found outline with {outline_context['total_slides']} slides")
        
        # Generate slides for each title in the outline
        for slide_index, slide_title in enumerate(outline_context['outline']):
            print(f"\nGenerating slide {slide_index + 1}: {slide_title}")
            
            # Create a session for this slide
            session = await session_service.create_session(
                app_name='slide_writer_app', 
                user_id=user_id,
                session_id=f"{presentation_id}_slide_{slide_index}"
            )
            
            # Prepare input for slide writer agent
            slide_input = {
                "title": slide_title,
                "assets": [],  # Could include relevant assets
                "constraints": {
                    "max_bullets": 4,
                    "max_words_per_bullet": 12
                }
            }
            
            # Run the agent
            content = types.Content(role='user', parts=[types.Part(text=json.dumps(slide_input))])
            
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
                    
                    # Parse slide response
                    try:
                        slide_data = json.loads(response_text)
                        
                        # Validate slide content
                        validation = await slide_writer_client.validate_slide_content(slide_data)
                        if not validation["valid"]:
                            print(f"Validation errors: {validation['errors']}")
                        if validation["warnings"]:
                            print(f"Validation warnings: {validation['warnings']}")
                        
                        # Store slide
                        stored_slide = await slide_writer_client.store_slide_content(
                            presentation_id, slide_index, slide_data
                        )
                        
                        print(f"Stored slide {slide_index + 1} (version {stored_slide['version']})")
                        print(f"  Title: {slide_data.get('title', '')}")
                        print(f"  Bullets: {len(slide_data.get('content', []))}")
                        print(f"  Notes length: {len(slide_data.get('speakerNotes', ''))} chars")
                        
                    except json.JSONDecodeError:
                        print(f"Agent response (not JSON): {response_text}")
                    
                    break
        
        # Show final slides summary
        print("\n=== Generated Slides Summary ===")
        slides = await slide_writer_client.get_slides_for_processing(presentation_id)
        for slide in slides:
            print(f"Slide {slide['slide_index'] + 1}: {slide['title']} (v{slide['version']})")
        
        # Update final status
        await slide_writer_client.update_presentation_status(presentation_id, "slides_completed")
        
        # Show presentation state
        state = await slide_writer_client.get_presentation_state(presentation_id)
        if state:
            print(f"\nFinal status: {state['metadata']['status']}")
            print(f"Total slides generated: {len(state['slides'])}")
    
    finally:
        await slide_writer_client.close()


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")