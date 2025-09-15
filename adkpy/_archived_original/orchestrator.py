"""
Orchestrator for the Presentation Generation Workflow

This module defines the main orchestrator that manages the sequence of agent calls
to generate a complete presentation from a user's initial prompt. It demonstrates
a practical implementation of Agent-to-Agent (A2A) communication.
"""

from typing import Any, Dict, List

# Import all agent classes and their data models
from . import (
    ClarifierAgent, ClarifierInput,
    OutlineAgent, OutlineInput,
    ResearchAgent, ResearchInput,
    SlideWriterAgent, SlideWriterInput,
    CriticAgent, CriticInput,
    DesignAgent, DesignInput,
    NotesPolisherAgent, NotesPolisherInput,
    ScriptWriterAgent, ScriptWriterInput
)


class Orchestrator:
    """
    Manages the end-to-end workflow for creating a presentation by coordinating
    multiple specialized agents.
    """

    def __init__(self, model: str = "googleai/gemini-2.5-flash"):
        """
        Initializes the orchestrator and all required agents.
        """
        print("Initializing agents...")
        self.model = model
        self.clarifier = ClarifierAgent(model=self.model)
        self.researcher = ResearchAgent(model=self.model)
        self.outliner = OutlineAgent(model=self.model)
        self.slide_writer = SlideWriterAgent(model=self.model)
        self.critic = CriticAgent(model=self.model)
        self.designer = DesignAgent(model=self.model)
        self.notes_polisher = NotesPolisherAgent(model=self.model)
        self.script_writer = ScriptWriterAgent(model=self.model)
        print("All agents initialized.")

    def run(self, initial_prompt: str, assets: List[Dict[str, Any]] = None):
        """
        Executes the full presentation generation workflow.

        Args:
            initial_prompt: The user's initial, high-level goal for the presentation.
            assets: An optional list of assets (documents, etc.) to ground the content.
        """
        print("\n--- Starting Presentation Workflow ---")
        
        # Step 1: Clarify Goals
        refined_goals = self._clarify_goals(initial_prompt, assets)

        # Step 2: Research Design Rules
        design_rules = self._research_design_rules()

        # Step 3: Generate Outline
        slide_titles = self._generate_outline(refined_goals)

        # Step 4: Generate and Refine Slides
        final_slides = self._generate_slides(slide_titles, design_rules, assets)

        # Step 5: Assemble Final Script
        final_script = self._write_script(final_slides, assets)

        # Step 6: Final Output
        print("\n[Step 6/6] Workflow Complete!")
        print("-" * 50)
        print("FINAL PRESENTATION SCRIPT:")
        print(final_script)
        print("-" * 50)
        
        return {
            "final_script": final_script,
            "slides": final_slides
        }

    def _clarify_goals(self, prompt: str, assets: List[Dict[str, Any]]) -> str:
        print("\n[Step 1/6] Clarifying user goals...")
        clarifier_input = ClarifierInput(
            history=[], initialInput={"text": prompt}, newFiles=assets
        )
        clarifier_result = self.clarifier.run(clarifier_input).data
        refined_goals = clarifier_result.get('response', prompt)
        print(f"Clarified Goals: {refined_goals}")
        return refined_goals

    def _research_design_rules(self) -> List[str]:
        print("\n[Step 2/6] Researching best practices for design...")
        research_input = ResearchInput(query="presentation background design best practices")
        research_result = self.researcher.run(research_input)
        design_rules = research_result.data['rules']
        print(f"Found {len(design_rules)} design rules.")
        return design_rules

    def _generate_outline(self, goals: str) -> List[str]:
        print("\n[Step 3/6] Generating presentation outline...")
        outline_input = OutlineInput(clarifiedContent=goals)
        outline_result = self.outliner.run(outline_input)
        slide_titles = outline_result.data['outline']
        print("Generated Outline:")
        for i, title in enumerate(slide_titles):
            print(f"  {i+1}. {title}")
        return slide_titles

    def _generate_slides(self, titles: List[str], design_rules: List[str], assets: List[Dict[str, Any]]) -> List[Dict]:
        print("\n[Step 4/6] Generating and refining individual slides...")
        final_slides = []
        for title in titles:
            print(f"\n  --- Processing Slide: {title} ---")
            
            # Write, critique, polish, and design each slide
            slide_writer_input = SlideWriterInput(title=title, assets=assets)
            draft_result = self.slide_writer.run(slide_writer_input).data
            
            critic_input = CriticInput(slideDraft=draft_result, assets=assets)
            critiqued_slide = self.critic.run(critic_input).data
            print(f"  Critiqued and corrected content.")
            
            notes_input = NotesPolisherInput(speakerNotes=critiqued_slide['speakerNotes'])
            polished_notes = self.notes_polisher.run(notes_input).data['rephrasedSpeakerNotes']
            critiqued_slide['speakerNotes'] = polished_notes
            print(f"  Polished speaker notes.")
            
            design_input = DesignInput(slide=critiqued_slide, researchRules=design_rules)
            design = self.designer.run(design_input).data
            critiqued_slide['design'] = design
            print(f"  Generated design of type '{design['type']}'.")
            
            final_slides.append(critiqued_slide)
        return final_slides

    def _write_script(self, slides: List[Dict], assets: List[Dict[str, Any]]) -> str:
        print("\n[Step 5/6] Assembling the final presenter script...")
        script_writer_input = ScriptWriterInput(slides=slides, assets=assets)
        script_result = self.script_writer.run(script_writer_input)
        final_script = script_result.data['script']
        print("Final script assembled.")
        return final_script

if __name__ == '__main__':
    # This is an example of how to run the orchestrator.
    user_prompt = "Create a short, professional presentation for a tech leadership audience on the key benefits of adopting a microservices architecture. Mention scalability, resilience, and independent deployment."
    
    example_assets = [
        {
            "name": "scalability_research.pdf",
            "text": "Microservices allow teams to scale individual components independently. If a payment service is under heavy load, it can be scaled up without affecting the user authentication or product catalog services. This leads to efficient resource utilization."
        },
        {
            "name": "devops_article.txt",
            "text": "A key advantage is fault isolation. An error in one microservice, such as a memory leak, is less likely to bring down the entire application. This resilience is crucial for high-availability systems."
        }
    ]
    
    orchestrator = Orchestrator()
    final_product = orchestrator.run(initial_prompt=user_prompt, assets=example_assets)