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
from design import agent

load_dotenv()

class DesignArangoClient(EnhancedArangoClient):
    """Design-specific ArangoDB client with visual design specifications management"""
    
    def __init__(self):
        super().__init__(agent_name="design")
    
    async def store_slide_design(self, presentation_id: str, slide_index: int, design_spec: Dict) -> Dict:
        """Store design specifications for a specific slide"""
        # Create a comprehensive design document
        design_doc = {
            "presentation_id": presentation_id,
            "slide_index": slide_index,
            "design_type": design_spec.get("type", "prompt"),  # "code" or "prompt"
            "background_spec": design_spec,
            "agent_source": self.agent_name,
            "created_at": design_spec.get("created_at")
        }
        
        # Store in design_specs collection with slide-specific key
        doc_key = f"{presentation_id}_slide_{slide_index}"
        design_doc["_key"] = doc_key
        
        try:
            result = self._collections['design_specs'].insert(design_doc, overwrite=True, return_new=True)
            self.logger.info(f"Stored design spec for slide {slide_index} in {presentation_id}")
            return result['new']
        except Exception as e:
            self.logger.error(f"Failed to store design spec for slide {slide_index}: {e}")
            raise
    
    async def store_presentation_theme(self, presentation_id: str, theme_spec: Dict) -> Dict:
        """Store overall presentation theme and design guidelines"""
        theme_doc = {
            "presentation_id": presentation_id,
            "theme_name": theme_spec.get("theme", "default"),
            "color_palette": theme_spec.get("colors", {}),
            "typography": theme_spec.get("typography", {}),
            "layout_guidelines": theme_spec.get("layout", {}),
            "brand_elements": theme_spec.get("branding", {}),
            "agent_source": self.agent_name
        }
        
        return await self.save_design_spec(presentation_id, theme_doc)
    
    async def generate_slide_backgrounds(self, presentation_id: str, theme: str = "brand", pattern: str = "gradient") -> Dict:
        """Generate background designs for all slides in the presentation"""
        slides = await self.get_latest_slides(presentation_id)
        generated_count = 0
        
        session_service = ArangoSessionService(self)
        root_agent = agent.root_agent
        runner = Runner(
            app_name='design_app',
            agent=root_agent,
            session_service=session_service,
            artifact_service=InMemoryArtifactService()
        )
        
        for slide in slides:
            try:
                # Create session for this design
                session = await session_service.create_session(
                    app_name='design_app',
                    user_id='system',
                    session_id=f"{presentation_id}_design_{slide['slide_index']}"
                )
                
                # Prepare design input
                design_input = {
                    "slide": {
                        "title": slide["title"],
                        "content": slide["content"],
                        "index": slide["slide_index"]
                    },
                    "theme": theme,
                    "pattern": pattern
                }
                
                # Run the agent
                content = types.Content(role='user', parts=[types.Part(text=json.dumps(design_input))])
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
                            design_response = json.loads(response_text)
                            
                            if design_response:
                                await self.store_slide_design(
                                    presentation_id, 
                                    slide["slide_index"], 
                                    design_response
                                )
                                generated_count += 1
                        except json.JSONDecodeError:
                            print(f"Failed to parse design for slide {slide['slide_index']}")
                        break
                        
            except Exception as e:
                print(f"Error generating design for slide {slide['slide_index']}: {e}")
        
        # Update presentation status
        if generated_count > 0:
            await self.update_presentation_status(presentation_id, "designs_generated")
        
        return {
            "generated_count": generated_count,
            "total_slides": len(slides),
            "success_rate": generated_count / len(slides) if slides else 0
        }
    
    async def get_slide_design(self, presentation_id: str, slide_index: int) -> Dict:
        """Get design specification for a specific slide"""
        doc_key = f"{presentation_id}_slide_{slide_index}"
        return self._collections['design_specs'].get(doc_key)
    
    async def get_presentation_designs(self, presentation_id: str) -> List[Dict]:
        """Get all slide designs for a presentation"""
        cursor = self._db.aql.execute('''
            FOR d IN design_specs 
            FILTER d.presentation_id == @pid AND d.slide_index != null
            SORT d.slide_index
            RETURN d
        ''', bind_vars={'pid': presentation_id})
        return list(cursor)


async def async_main():
    """Example usage of the design client"""
    design_client = DesignArangoClient()
    await design_client.connect()
    
    try:
        presentation_id = "test_presentation_001"
        
        # Generate backgrounds for all slides
        result = await design_client.generate_slide_backgrounds(
            presentation_id, 
            theme="brand", 
            pattern="gradient"
        )
        print(f"Generated designs for {result['generated_count']} out of {result['total_slides']} slides")
        print(f"Success rate: {result['success_rate']:.2%}")
        
        # Show generated designs
        designs = await design_client.get_presentation_designs(presentation_id)
        for design in designs:
            print(f"Slide {design['slide_index']}: {design['design_type']} design")
        
    finally:
        await design_client.close()


if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")