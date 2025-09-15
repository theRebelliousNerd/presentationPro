#!/usr/bin/env python3
"""
ADK Dev UI Server for PresentationPro

This script launches the ADK Dev UI for testing and evaluating our presentation agents.
Based on Google's InstaVibe ADK Multi-Agent codelab pattern.

Usage:
    python adk_dev_server.py [--port PORT]

Default port: 8100 (to avoid conflicts with other services)
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

# Add the agents directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

# Import ADK components
try:
    from google.adk import dev
except ImportError:
    print("ERROR: Google ADK not installed. Please install with:")
    print("  pip install google-adk")
    sys.exit(1)

# Import our agents
from agents.clarifier.agent import clarifier_agent
from agents.outline.agent import outline_agent
from agents.slide_writer.agent import slide_writer_agent
from agents.critic.agent import critic_agent
from agents.notes_polisher.agent import notes_polisher_agent
from agents.design.agent import design_agent
from agents.script_writer.agent import script_writer_agent
from agents.research.agent import research_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agent registry
AGENTS: Dict[str, Agent] = {
    "clarifier": clarifier_agent,
    "outline": outline_agent,
    "slide_writer": slide_writer_agent,
    "critic": critic_agent,
    "notes_polisher": notes_polisher_agent,
    "design": design_agent,
    "script_writer": script_writer_agent,
    "research": research_agent,
}

def create_app(port: int = 8100) -> FastAPI:
    """
    Create the ADK Dev UI FastAPI application.

    Args:
        port: Port number for the server

    Returns:
        FastAPI application instance
    """
    # Create the base FastAPI app
    app = FastAPI(
        title="PresentationPro ADK Dev UI",
        description="Development UI for testing and evaluating presentation agents",
        version="1.0.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Get the ADK Dev UI app
    dev_ui_app = dev.get_app(
        agents=list(AGENTS.values()),
        title="PresentationPro Agent Development",
        description="Test and evaluate presentation generation agents"
    )

    # Mount the dev UI
    app.mount("/adk", dev_ui_app)

    # Root endpoint
    @app.get("/")
    async def root():
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PresentationPro ADK Dev UI</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    text-align: center;
                    background: white;
                    padding: 3rem;
                    border-radius: 10px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 1rem;
                }}
                p {{
                    color: #666;
                    margin-bottom: 2rem;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    transition: transform 0.2s;
                }}
                .button:hover {{
                    transform: translateY(-2px);
                    background: #5a67d8;
                }}
                .info {{
                    margin-top: 2rem;
                    padding: 1rem;
                    background: #f7fafc;
                    border-radius: 5px;
                    text-align: left;
                }}
                .agent-list {{
                    list-style: none;
                    padding: 0;
                }}
                .agent-list li {{
                    padding: 0.5rem;
                    margin: 0.25rem 0;
                    background: #edf2f7;
                    border-radius: 3px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 PresentationPro ADK Dev UI</h1>
                <p>Interactive development environment for presentation agents</p>
                <a href="/adk" class="button">Launch Dev UI</a>

                <div class="info">
                    <h3>Available Agents:</h3>
                    <ul class="agent-list">
                        <li>📝 <strong>Clarifier</strong> - Refines presentation goals</li>
                        <li>📋 <strong>Outline</strong> - Creates presentation structure</li>
                        <li>✍️ <strong>Slide Writer</strong> - Generates slide content</li>
                        <li>🔍 <strong>Critic</strong> - Reviews and improves slides</li>
                        <li>💬 <strong>Notes Polisher</strong> - Enhances speaker notes</li>
                        <li>🎨 <strong>Design</strong> - Creates visual designs</li>
                        <li>📜 <strong>Script Writer</strong> - Assembles presenter script</li>
                        <li>🔬 <strong>Research</strong> - Gathers background information</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """)

    # Health check endpoint
    @app.get("/health")
    async def health():
        return JSONResponse({
            "status": "healthy",
            "service": "adk-dev-ui",
            "port": port,
            "agents": list(AGENTS.keys())
        })

    # Agent info endpoint
    @app.get("/agents")
    async def get_agents():
        return JSONResponse({
            "agents": [
                {
                    "name": name,
                    "description": agent.description if hasattr(agent, 'description') else f"{name} agent",
                    "model": agent.model if hasattr(agent, 'model') else "gemini-2.0-flash"
                }
                for name, agent in AGENTS.items()
            ]
        })

    return app

def main():
    """Main entry point for the ADK Dev UI server."""
    parser = argparse.ArgumentParser(
        description="Launch the ADK Dev UI for PresentationPro agents"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8100,
        help="Port to run the server on (default: 8100)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    # Print startup banner
    print("+" + "-" * 77 + "+")
    print("|" + " " * 77 + "|")
    print("|" + "ADK Dev UI Server Started".center(77) + "|")
    print("|" + " " * 77 + "|")
    print("|" + f"For local testing, access at http://localhost:{args.port}/adk".center(77) + "|")
    print("|" + " " * 77 + "|")
    print("+" + "-" * 77 + "+")

    # Create the app
    app = create_app(port=args.port)

    # Run the server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()