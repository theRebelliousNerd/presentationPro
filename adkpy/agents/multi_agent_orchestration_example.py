"""
Multi-Agent ArangoDB Integration Example

This example demonstrates how all ADK agents work together with ArangoDB
to create a complete presentation through coordinated multi-agent writes.

Run this example to see the full presentation generation pipeline:
1. Clarifier -> gathers requirements
2. Outline -> creates structure  
3. Slide Writer -> generates content
4. Critic -> reviews and corrects
5. Notes Polisher -> enhances speaker notes
6. Design -> creates visual specs
7. Script Writer -> generates final script

All agents store their work in ArangoDB with proper coordination.
"""

import asyncio
import json
import uuid
from typing import Dict, List
from datetime import datetime

# Import all agent clients
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from clarifier.ArangoClient import ClarifierArangoClient
from outline.ArangoClient import OutlineArangoClient  
from slide_writer.ArangoClient import SlideWriterArangoClient
from notes_polisher.ArangoClient import NotesPolisherArangoClient
from design.ArangoClient import DesignArangoClient
from script_writer.ArangoClient import ScriptWriterArangoClient
from critic.ArangoClient import CriticArangoClient


class PresentationOrchestrator:
    """Orchestrates the complete presentation generation pipeline"""
    
    def __init__(self):
        self.agents = {}
        self.presentation_id = None
        self.user_id = "demo_user"
    
    async def initialize_agents(self):
        """Initialize all agent clients"""
        agent_classes = {
            'clarifier': ClarifierArangoClient,
            'outline': OutlineArangoClient,
            'slide_writer': SlideWriterArangoClient,
            'notes_polisher': NotesPolisherArangoClient,
            'design': DesignArangoClient,
            'script_writer': ScriptWriterArangoClient,
            'critic': CriticArangoClient
        }
        
        for agent_name, agent_class in agent_classes.items():
            try:
                agent = agent_class()
                await agent.connect()
                self.agents[agent_name] = agent
                print(f"✓ Initialized {agent_name} agent")
            except Exception as e:
                print(f"✗ Failed to initialize {agent_name} agent: {e}")
                raise
    
    async def cleanup_agents(self):
        """Clean up all agent connections"""
        for agent_name, agent in self.agents.items():
            try:
                await agent.close()
                print(f"✓ Closed {agent_name} agent")
            except Exception as e:
                print(f"✗ Error closing {agent_name} agent: {e}")
    
    async def create_presentation(self, title: str = None) -> str:
        """Create a new presentation and return its ID"""
        self.presentation_id = f"demo_presentation_{uuid.uuid4().hex[:8]}"
        
        # Create presentation in all agents (they'll handle duplicates gracefully)
        for agent_name, agent in self.agents.items():
            await agent.create_presentation(self.presentation_id, self.user_id)
        
        print(f"📝 Created presentation: {self.presentation_id}")
        return self.presentation_id
    
    async def run_clarification_phase(self, initial_request: str) -> Dict:
        """Phase 1: Clarify presentation requirements"""
        print("\n🤔 Phase 1: Clarifying requirements...")
        
        clarifier = self.agents['clarifier']
        
        # Simulate clarification process with some pre-defined exchanges
        clarifications = [
            {
                "user": initial_request,
                "assistant": "What is your target audience and their technical background?"
            },
            {
                "user": "Software developers with 2-5 years experience",
                "assistant": "How long should the presentation be and what's the main goal?"
            },
            {
                "user": "20 minutes, to introduce AI concepts and practical applications",
                "assistant": "Perfect! I'll create a presentation about AI fundamentals and practical applications for mid-level developers in a 20-minute format."
            }
        ]
        
        # Store clarification history
        for exchange in clarifications:
            await clarifier.add_clarification(self.presentation_id, "user", exchange["user"])
            await clarifier.add_clarification(self.presentation_id, "assistant", exchange["assistant"])
        
        # Store final clarified goals
        final_summary = "Create a 20-minute technical presentation about AI fundamentals and practical applications for software developers with 2-5 years experience. Cover machine learning basics, real-world use cases, and implementation considerations."
        
        await clarifier.finalize_clarification(self.presentation_id, final_summary)
        
        print(f"✓ Clarification completed with {len(clarifications)} exchanges")
        return {"final_summary": final_summary}
    
    async def run_outline_phase(self, clarified_content: str) -> Dict:
        """Phase 2: Generate presentation outline"""
        print("\n📋 Phase 2: Creating outline...")
        
        outline_agent = self.agents['outline']
        
        # Create a structured outline
        outline = [
            "Introduction: AI in Software Development",
            "Machine Learning Fundamentals",
            "Practical AI Applications",
            "Implementation Strategies",
            "Tools and Frameworks",
            "Common Challenges and Solutions",
            "Future Trends",
            "Getting Started: Next Steps"
        ]
        
        # Validate outline structure
        validation = await outline_agent.validate_outline_structure(outline)
        if not validation["valid"]:
            print(f"⚠️ Outline validation errors: {validation['errors']}")
        
        # Store outline
        await outline_agent.store_presentation_outline(
            self.presentation_id, outline, clarified_content
        )
        
        print(f"✓ Outline created with {len(outline)} slides")
        return {"outline": outline, "validation": validation}
    
    async def run_slide_generation_phase(self) -> Dict:
        """Phase 3: Generate slide content"""
        print("\n✍️ Phase 3: Generating slide content...")
        
        slide_writer = self.agents['slide_writer']
        
        # Get outline for context
        outline_context = await slide_writer.get_outline_context(self.presentation_id)
        outline = outline_context["outline"]
        
        generated_slides = []
        
        # Generate content for each slide
        for slide_index, slide_title in enumerate(outline):
            print(f"  Generating slide {slide_index + 1}: {slide_title}")
            
            # Create realistic slide content
            slide_content = await self._generate_sample_slide_content(slide_title, slide_index)
            
            # Validate content
            validation = await slide_writer.validate_slide_content(slide_content)
            if validation["warnings"]:
                print(f"    ⚠️ Warnings: {len(validation['warnings'])}")
            
            # Store slide
            stored_slide = await slide_writer.store_slide_content(
                self.presentation_id, slide_index, slide_content
            )
            
            generated_slides.append({
                "index": slide_index,
                "title": slide_title,
                "version": stored_slide["version"]
            })
        
        print(f"✓ Generated {len(generated_slides)} slides")
        return {"slides": generated_slides}
    
    async def run_critic_phase(self) -> Dict:
        """Phase 4: Review and correct content"""
        print("\n🔍 Phase 4: Reviewing content...")
        
        critic = self.agents['critic']
        
        # Review entire presentation
        review_summary = await critic.review_entire_presentation(self.presentation_id)
        
        print(f"✓ Reviewed {review_summary['slides_reviewed']} slides")
        print(f"  Total corrections: {review_summary['total_corrections']}")
        
        return review_summary
    
    async def run_enhancement_phases(self) -> Dict:
        """Phase 5: Enhance with design, notes, and script"""
        print("\n🎨 Phase 5: Enhancing presentation...")
        
        results = {}
        
        # Notes enhancement
        print("  Enhancing speaker notes...")
        notes_polisher = self.agents['notes_polisher']
        notes_result = await notes_polisher.batch_enhance_notes(
            self.presentation_id, tone="professional"
        )
        results['notes'] = notes_result
        print(f"    ✓ Enhanced {notes_result['enhanced_count']} sets of notes")
        
        # Design generation
        print("  Generating visual designs...")
        design_agent = self.agents['design']
        design_result = await design_agent.generate_slide_backgrounds(
            self.presentation_id, theme="brand", pattern="gradient"
        )
        results['design'] = design_result
        print(f"    ✓ Generated {design_result['generated_count']} designs")
        
        # Script generation
        print("  Creating presentation script...")
        script_writer = self.agents['script_writer']
        script_result = await script_writer.generate_presentation_script(
            self.presentation_id
        )
        results['script'] = script_result
        
        if script_result.get('success'):
            metrics = await script_writer.analyze_script_metrics(self.presentation_id)
            print(f"    ✓ Generated script: {metrics['word_count']} words, ~{metrics['estimated_duration_minutes']} min")
        else:
            print(f"    ✗ Script generation failed")
        
        return results
    
    async def _generate_sample_slide_content(self, title: str, index: int) -> Dict:
        """Generate realistic sample slide content"""
        content_templates = {
            0: {  # Introduction
                "content": [
                    "AI is transforming software development",
                    "From automation to intelligent features",
                    "Practical applications in daily work",
                    "Why developers should care now"
                ],
                "speakerNotes": "Welcome everyone. Today we'll explore how AI is changing software development and why it matters for developers like us. We'll focus on practical applications you can start using immediately.",
                "imagePrompt": "Modern tech workspace with AI and code visualization, clean professional style"
            },
            1: {  # ML Fundamentals
                "content": [
                    "Machine learning: pattern recognition in data",
                    "Supervised vs unsupervised learning",
                    "Training models with examples",
                    "Key algorithms developers should know"
                ],
                "speakerNotes": "Let's start with the basics. Machine learning is fundamentally about finding patterns in data. Think of it as teaching computers to recognize patterns the same way humans do.",
                "imagePrompt": "Abstract visualization of data patterns and neural networks, educational diagram style"
            }
        }
        
        # Use template if available, otherwise generate generic content
        if index in content_templates:
            template = content_templates[index]
        else:
            template = {
                "content": [
                    f"Key concept for {title}",
                    "Practical implementation approach",
                    "Benefits and considerations",
                    "Real-world examples"
                ],
                "speakerNotes": f"This slide covers {title.lower()}. We'll discuss the practical aspects and how this applies to your development work.",
                "imagePrompt": f"Professional illustration representing {title.lower()}, clean technical style"
            }
        
        return {
            "title": title,
            "content": template["content"],
            "speakerNotes": template["speakerNotes"],
            "imagePrompt": template["imagePrompt"]
        }
    
    async def generate_final_report(self) -> Dict:
        """Generate comprehensive report of the presentation"""
        print("\n📊 Generating final report...")
        
        # Get presentation state from any agent (they all have the same data)
        base_agent = self.agents['clarifier']
        state = await base_agent.get_presentation_state(self.presentation_id)
        
        # Health check all agents
        health_checks = {}
        for agent_name, agent in self.agents.items():
            health_checks[agent_name] = await agent.health_check()
        
        report = {
            "presentation_id": self.presentation_id,
            "status": state['metadata']['status'] if state else "unknown",
            "created_at": state['metadata']['created_at'] if state else None,
            "components": {
                "clarifications": len(state.get('clarifications', [])),
                "outline_slides": len(state['outline']['outline']) if state.get('outline') else 0,
                "generated_slides": len(state.get('slides', [])),
            },
            "agent_health": health_checks,
            "timestamp": datetime.now().isoformat()
        }
        
        return report


async def main():
    """Run the complete multi-agent presentation generation example"""
    print("🚀 Starting Multi-Agent Presentation Generation Example")
    print("=" * 60)
    
    orchestrator = PresentationOrchestrator()
    
    try:
        # Initialize all agents
        print("Initializing agents...")
        await orchestrator.initialize_agents()
        
        # Create presentation
        presentation_id = await orchestrator.create_presentation()
        
        # Run the complete pipeline
        initial_request = "I need a presentation about AI for developers"
        
        # Phase 1: Clarification
        clarification_result = await orchestrator.run_clarification_phase(initial_request)
        
        # Phase 2: Outline
        outline_result = await orchestrator.run_outline_phase(
            clarification_result["final_summary"]
        )
        
        # Phase 3: Content Generation
        slides_result = await orchestrator.run_slide_generation_phase()
        
        # Phase 4: Review
        review_result = await orchestrator.run_critic_phase()
        
        # Phase 5: Enhancement
        enhancement_result = await orchestrator.run_enhancement_phases()
        
        # Final Report
        final_report = await orchestrator.generate_final_report()
        
        print("\n🎉 Presentation Generation Complete!")
        print("=" * 60)
        print(f"Presentation ID: {presentation_id}")
        print(f"Status: {final_report['status']}")
        print(f"Components generated:")
        print(f"  - Clarifications: {final_report['components']['clarifications']}")
        print(f"  - Outline slides: {final_report['components']['outline_slides']}")
        print(f"  - Generated slides: {final_report['components']['generated_slides']}")
        
        print(f"\nAgent Health Status:")
        for agent_name, health in final_report['agent_health'].items():
            status = "✓" if health['healthy'] else "✗"
            print(f"  {status} {agent_name}: {'Healthy' if health['healthy'] else health.get('error', 'Unknown error')}")
        
        print(f"\n📄 Full report saved to: presentation_report_{presentation_id}.json")
        
        # Save detailed report
        with open(f"presentation_report_{presentation_id}.json", "w") as f:
            json.dump(final_report, f, indent=2)
        
        print("\n✨ Multi-agent ArangoDB integration demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during presentation generation: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up connections
        print("\nCleaning up connections...")
        await orchestrator.cleanup_agents()
        print("✓ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())