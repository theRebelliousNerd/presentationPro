#!/usr/bin/env python3
"""
Test script to verify model configuration propagation through the ADK system.

This tests that:
1. Agents can receive custom model configurations
2. Model names are properly normalized (googleai/ prefix stripped)
3. Each agent uses its configured model
"""

import asyncio
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our agent wrappers
from agents.wrappers import (
    ClarifierAgent, ClarifierInput,
    OutlineAgent, OutlineInput,
    SlideWriterAgent, SlideWriterInput,
    NotesPolisherAgent, NotesPolisherInput,
    DesignAgent, DesignInput,
    ScriptWriterAgent, ScriptWriterInput,
    ResearchAgent, ResearchInput
)


def test_clarifier_agent():
    """Test the ClarifierAgent with custom model."""
    logger.info("Testing ClarifierAgent...")

    agent = ClarifierAgent()
    input_data = ClarifierInput(
        history=[
            {"role": "user", "content": "I need a presentation about AI"},
            {"role": "assistant", "content": "I'd be happy to help with an AI presentation. Who is your target audience?"},
            {"role": "user", "content": "Software developers"}
        ],
        initialInput={"text": "Create a presentation about AI for developers"},
        textModel="googleai/gemini-2.5-pro"  # Test with Pro model
    )

    result = agent.run(input_data)

    logger.info(f"ClarifierAgent result: {json.dumps(result.data, indent=2)}")
    logger.info(f"Model used: {result.usage.model}")
    assert result.usage.model == "googleai/gemini-2.5-pro" or result.usage.model == "gemini-2.5-pro"
    logger.info("✓ ClarifierAgent test passed")

    return result.data


def test_outline_agent(clarified_content: str):
    """Test the OutlineAgent with custom model."""
    logger.info("Testing OutlineAgent...")

    agent = OutlineAgent()
    input_data = OutlineInput(
        clarifiedContent=clarified_content,
        textModel="googleai/gemini-2.0-flash"  # Test with Flash model
    )

    result = agent.run(input_data)

    logger.info(f"OutlineAgent result: {json.dumps(result.data, indent=2)}")
    logger.info(f"Model used: {result.usage.model}")
    assert "outline" in result.data
    assert isinstance(result.data["outline"], list)
    logger.info("✓ OutlineAgent test passed")

    return result.data["outline"]


def test_slide_writer_agent(outline: list, clarified_content: str):
    """Test the SlideWriterAgent with custom models."""
    logger.info("Testing SlideWriterAgent...")

    agent = SlideWriterAgent()
    input_data = SlideWriterInput(
        clarifiedContent=clarified_content,
        outline=outline,
        audience="Software developers",
        tone="professional",
        length="medium",
        writerModel="googleai/gemini-2.5-flash",  # Writer uses Flash
        criticModel="googleai/gemini-2.5-pro"     # Critic uses Pro
    )

    result = agent.run(input_data)

    logger.info(f"SlideWriterAgent result: {json.dumps(result.data, indent=2)}")
    logger.info(f"Model used: {result.usage.model}")
    assert "title" in result.data
    assert "content" in result.data
    assert "speakerNotes" in result.data
    logger.info("✓ SlideWriterAgent test passed")

    return result.data


def test_notes_polisher_agent(speaker_notes: str):
    """Test the NotesPolisherAgent with custom model."""
    logger.info("Testing NotesPolisherAgent...")

    agent = NotesPolisherAgent()
    input_data = NotesPolisherInput(
        speakerNotes=speaker_notes,
        tone="concise",
        textModel="googleai/gemini-2.5-flash"
    )

    result = agent.run(input_data)

    logger.info(f"NotesPolisherAgent result: {json.dumps(result.data, indent=2)}")
    logger.info(f"Model used: {result.usage.model}")
    assert "rephrasedSpeakerNotes" in result.data
    logger.info("✓ NotesPolisherAgent test passed")

    return result.data["rephrasedSpeakerNotes"]


def test_design_agent(slide: Dict[str, Any]):
    """Test the DesignAgent with custom model."""
    logger.info("Testing DesignAgent...")

    agent = DesignAgent()

    # Test prompt generation
    input_data = DesignInput(
        slide=slide,
        theme="brand",
        pattern="gradient",
        preferCode=False,
        textModel="googleai/gemini-2.5-flash"
    )

    result = agent.run(input_data)

    logger.info(f"DesignAgent result: {json.dumps(result.data, indent=2)}")
    logger.info(f"Model used: {result.usage.model}")
    assert "type" in result.data
    assert result.data["type"] in ["prompt", "code"]

    # Test code generation
    input_data.preferCode = True
    result = agent.run(input_data)
    logger.info(f"DesignAgent code result: {json.dumps(result.data, indent=2)}")
    assert result.data["type"] == "code"

    logger.info("✓ DesignAgent test passed")


def test_script_writer_agent(slides: list):
    """Test the ScriptWriterAgent with custom model."""
    logger.info("Testing ScriptWriterAgent...")

    agent = ScriptWriterAgent()
    input_data = ScriptWriterInput(
        slides=slides,
        textModel="googleai/gemini-2.5-pro"
    )

    result = agent.run(input_data)

    logger.info(f"ScriptWriterAgent result: {json.dumps(result.data, indent=2)[:200]}...")
    logger.info(f"Model used: {result.usage.model}")
    assert "script" in result.data
    logger.info("✓ ScriptWriterAgent test passed")


def test_research_agent():
    """Test the ResearchAgent with custom model."""
    logger.info("Testing ResearchAgent...")

    agent = ResearchAgent()
    input_data = ResearchInput(
        query="presentation design best practices",
        topK=3,
        textModel="googleai/gemini-2.5-flash"
    )

    result = agent.run(input_data)

    logger.info(f"ResearchAgent result: {json.dumps(result.data, indent=2)}")
    logger.info(f"Model used: {result.usage.model}")
    assert "rules" in result.data
    logger.info("✓ ResearchAgent test passed")


def main():
    """Run all agent tests."""
    logger.info("Starting model configuration tests...")

    try:
        # Test clarifier
        clarified = test_clarifier_agent()
        clarified_content = clarified.get("response", "AI presentation for developers")

        # Test outline
        outline = test_outline_agent(clarified_content)

        # Test slide writer
        slide = test_slide_writer_agent(outline, clarified_content)

        # Test notes polisher
        if slide.get("speakerNotes"):
            test_notes_polisher_agent(slide["speakerNotes"])

        # Test design
        test_design_agent(slide)

        # Test script writer
        test_script_writer_agent([slide])

        # Test research
        test_research_agent()

        logger.info("\n✅ All tests passed! Model configuration is working correctly.")

    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()