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
from critic import agent

load_dotenv()

class CriticArangoClient(EnhancedArangoClient):
    """Critic-specific ArangoDB client with quality assurance and review management"""
    
    def __init__(self):
        super().__init__(agent_name="critic")
    
    async def review_slide(self, presentation_id: str, slide_index: int, assets: List[Dict] = None) -> Dict:
        """Review and correct a single slide"""
        # Get the latest slide version
        slides = await self.get_latest_slides(presentation_id)
        target_slide = None
        
        for slide in slides:
            if slide["slide_index"] == slide_index:
                target_slide = slide
                break
        
        if not target_slide:
            raise ValueError(f"Slide {slide_index} not found in presentation {presentation_id}")
        
        # Set up the agent
        session_service = ArangoSessionService(self)
        root_agent = agent.root_agent
        runner = Runner(
            app_name='critic_app',
            agent=root_agent,
            session_service=session_service,
            artifact_service=InMemoryArtifactService()
        )
        
        # Create session
        session = await session_service.create_session(
            app_name='critic_app',
            user_id='system',
            session_id=f"{presentation_id}_review_{slide_index}"
        )
        
        # Prepare review input
        slide_draft = {
            "title": target_slide["title"],
            "content": target_slide["content"],
            "speakerNotes": target_slide["speaker_notes"],
            "imagePrompt": target_slide["image_prompt"]
        }
        
        review_input = {
            "slideDraft": slide_draft,
            "assets": assets or []
        }
        
        try:
            # Run the agent
            content = types.Content(role='user', parts=[types.Part(text=json.dumps(review_input))])
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
                        corrected_slide = json.loads(response_text)
                        
                        # Store the review and corrections
                        review_data = {
                            "original_slide": slide_draft,
                            "corrected_slide": corrected_slide,
                            "corrections_applied": self._identify_corrections(slide_draft, corrected_slide)
                        }
                        
                        stored_review = await self.save_review(presentation_id, slide_index, review_data)
                        
                        # Create new slide version with corrections
                        corrected_slide_content = SlideContent(
                            presentation_id=presentation_id,
                            slide_index=slide_index,
                            title=corrected_slide["title"],
                            content=corrected_slide["content"],
                            speaker_notes=corrected_slide["speakerNotes"],
                            image_prompt=corrected_slide["imagePrompt"],
                            agent_source="critic"
                        )
                        
                        new_slide_version = await self.save_slide(corrected_slide_content)
                        
                        return {
                            "success": True,
                            "review_stored": stored_review,
                            "new_slide_version": new_slide_version,
                            "corrections_count": len(review_data["corrections_applied"])
                        }
                        
                    except json.JSONDecodeError:
                        print("Failed to parse critic response")
                    break
        
        except Exception as e:
            print(f"Error reviewing slide: {e}")
        
        return {
            "success": False,
            "error": "Slide review failed"
        }
    
    def _identify_corrections(self, original: Dict, corrected: Dict) -> List[Dict]:
        """Identify what corrections were made"""
        corrections = []
        
        # Check title changes
        if original.get("title") != corrected.get("title"):
            corrections.append({
                "field": "title",
                "original": original.get("title"),
                "corrected": corrected.get("title"),
                "type": "content_change"
            })
        
        # Check content changes
        orig_content = original.get("content", [])
        corr_content = corrected.get("content", [])
        
        if orig_content != corr_content:
            corrections.append({
                "field": "content",
                "original": orig_content,
                "corrected": corr_content,
                "type": "bullet_points_change",
                "details": {
                    "original_count": len(orig_content),
                    "corrected_count": len(corr_content)
                }
            })
        
        # Check speaker notes changes
        if original.get("speakerNotes") != corrected.get("speakerNotes"):
            corrections.append({
                "field": "speakerNotes",
                "original": original.get("speakerNotes"),
                "corrected": corrected.get("speakerNotes"),
                "type": "notes_refinement"
            })
        
        # Check image prompt changes
        if original.get("imagePrompt") != corrected.get("imagePrompt"):
            corrections.append({
                "field": "imagePrompt",
                "original": original.get("imagePrompt"),
                "corrected": corrected.get("imagePrompt"),
                "type": "visual_alignment"
            })
        
        return corrections
    
    async def review_entire_presentation(self, presentation_id: str, assets: List[Dict] = None) -> Dict:
        """Review and correct all slides in the presentation"""
        slides = await self.get_latest_slides(presentation_id)
        reviewed_count = 0
        total_corrections = 0
        
        review_summary = {
            "presentation_id": presentation_id,
            "slides_reviewed": 0,
            "total_corrections": 0,
            "slide_reviews": []
        }
        
        for slide in sorted(slides, key=lambda x: x["slide_index"]):
            try:
                result = await self.review_slide(presentation_id, slide["slide_index"], assets)
                
                if result["success"]:
                    reviewed_count += 1
                    corrections_count = result["corrections_count"]
                    total_corrections += corrections_count
                    
                    review_summary["slide_reviews"].append({
                        "slide_index": slide["slide_index"],
                        "corrections_count": corrections_count,
                        "new_version": result["new_slide_version"]["version"]
                    })
                
            except Exception as e:
                print(f"Error reviewing slide {slide['slide_index']}: {e}")
        
        review_summary["slides_reviewed"] = reviewed_count
        review_summary["total_corrections"] = total_corrections
        
        # Update presentation status
        if reviewed_count > 0:
            await self.update_presentation_status(presentation_id, "reviewed")
        
        return review_summary
    
    async def get_review_history(self, presentation_id: str) -> List[Dict]:
        """Get all reviews for a presentation"""
        cursor = self._db.aql.execute('''
            FOR r IN reviews 
            FILTER r.presentation_id == @pid 
            SORT r.slide_index, r.created_at DESC
            RETURN r
        ''', bind_vars={'pid': presentation_id})
        return list(cursor)
    
    async def get_slide_review(self, presentation_id: str, slide_index: int) -> Dict:
        """Get the latest review for a specific slide"""
        doc_key = f"{presentation_id}_{slide_index}_{self.agent_name}"
        return self._collections['reviews'].get(doc_key)


async def async_main():
    """Example usage of the critic client"""
    critic_client = CriticArangoClient()
    await critic_client.connect()
    
    try:
        presentation_id = "test_presentation_001"
        
        # Review entire presentation
        review_summary = await critic_client.review_entire_presentation(presentation_id)
        
        print(f"Review Summary:")
        print(f"  Slides reviewed: {review_summary['slides_reviewed']}")
        print(f"  Total corrections: {review_summary['total_corrections']}")
        
        for slide_review in review_summary["slide_reviews"]:
            print(f"  Slide {slide_review['slide_index']}: {slide_review['corrections_count']} corrections (v{slide_review['new_version']})")
        
        # Show review history
        history = await critic_client.get_review_history(presentation_id)
        print(f"\nTotal reviews in history: {len(history)}")
        
    finally:
        await critic_client.close()


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")