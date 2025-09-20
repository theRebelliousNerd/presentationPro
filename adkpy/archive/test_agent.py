import pytest

pytest.skip("Legacy ADK dev helpers not available", allow_module_level=True)
pytestmark = pytest.mark.skip(reason="Legacy ADK dev helpers not available")

"""
Simple test agent for ADK Dev UI
"""

from google.adk.agents import Agent

# Create a simple test agent
test_agent = Agent(
    name="test_agent",
    model="gemini-2.0-flash",
    description="A simple test agent for ADK Dev UI testing",
    instruction="""
    You are a helpful assistant that can answer questions about presentations.
    When asked about presentation topics, provide thoughtful suggestions.
    Always respond in a friendly and professional manner.
    """
)

# Create our presentation agents as simple ADK agents for testing
clarifier_agent = Agent(
    name="clarifier",
    model="gemini-2.0-flash",
    description="Refines presentation goals through targeted Q&A",
    instruction="""
    You are a Clarifier agent. Your role is to ask targeted questions to help refine
    a user's presentation request. Ask ONE question at a time to gather information about:
    - Target audience
    - Presentation length
    - Key topics to cover
    - Tone and style preferences
    - Success criteria

    When you have enough information, provide a clear summary of the presentation goals.
    """
)

outline_agent = Agent(
    name="outline",
    model="gemini-2.0-flash",
    description="Creates presentation structure and outline",
    instruction="""
    You are an Outline agent. Given presentation goals and requirements, create a
    well-structured outline that includes:
    - Title slide
    - Introduction with hook
    - Main content sections with logical flow
    - Conclusion with call to action
    - Q&A slide

    Format your response as a structured outline with clear section headers.
    """
)

slide_writer_agent = Agent(
    name="slide_writer",
    model="gemini-2.0-flash",
    description="Generates detailed slide content",
    instruction="""
    You are a Slide Writer agent. Given an outline and specific slide requirements,
    generate compelling slide content including:
    - Engaging headlines
    - Key bullet points (3-5 per slide)
    - Speaker notes
    - Suggested visuals or diagrams

    Keep content concise and impactful.
    """
)

# Make agents available for ADK
root_agent = test_agent  # Default agent
agents = [clarifier_agent, outline_agent, slide_writer_agent]
