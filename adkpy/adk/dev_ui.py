"""
ADK Dev UI Module

Provides development UI capabilities for testing and debugging ADK agents.
"""

from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import logging

logger = logging.getLogger(__name__)


def get_dev_ui_server(
    agents: Optional[List[Any]] = None,
    host: str = "0.0.0.0",
    port: int = 8000,
    title: str = "ADK Dev UI"
) -> FastAPI:
    """
    Create a FastAPI server with ADK Dev UI capabilities.

    Args:
        agents: List of agents to expose in the UI
        host: Server host address
        port: Server port
        title: UI title

    Returns:
        FastAPI application instance
    """
    app = FastAPI(title=title, version="1.0.0")

    # Store agents in app state
    app.state.agents = agents or []

    @app.get("/", response_class=HTMLResponse)
    async def dev_ui_home():
        """Serve the dev UI home page."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>ADK Dev UI</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                h1 {
                    color: #333;
                    border-bottom: 2px solid #4CAF50;
                    padding-bottom: 10px;
                }
                .container {
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-top: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .agent-list {
                    list-style: none;
                    padding: 0;
                }
                .agent-item {
                    padding: 10px;
                    margin: 10px 0;
                    background: #f9f9f9;
                    border-radius: 4px;
                    border-left: 4px solid #4CAF50;
                }
                .agent-name {
                    font-weight: bold;
                    color: #2c3e50;
                }
                .agent-description {
                    color: #666;
                    margin-top: 5px;
                }
                .status {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    background: #4CAF50;
                    color: white;
                    font-size: 0.85em;
                }
                .test-area {
                    margin-top: 20px;
                }
                textarea {
                    width: 100%;
                    min-height: 100px;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-family: monospace;
                }
                button {
                    background: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-top: 10px;
                }
                button:hover {
                    background: #45a049;
                }
                .response {
                    background: #f0f0f0;
                    padding: 10px;
                    border-radius: 4px;
                    margin-top: 10px;
                    white-space: pre-wrap;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <h1>🤖 ADK Development UI</h1>

            <div class="container">
                <h2>System Status</h2>
                <p>Status: <span class="status">✓ Running</span></p>
                <p>Agents Loaded: <span id="agent-count">0</span></p>
            </div>

            <div class="container">
                <h2>Available Agents</h2>
                <ul class="agent-list" id="agent-list">
                    <li class="agent-item">
                        <div class="agent-name">No agents loaded</div>
                        <div class="agent-description">Please configure agents to see them here</div>
                    </li>
                </ul>
            </div>

            <div class="container">
                <h2>Test Console</h2>
                <div class="test-area">
                    <textarea id="test-input" placeholder="Enter test input JSON here..."></textarea>
                    <button onclick="runTest()">Run Test</button>
                    <div id="response" class="response" style="display:none;"></div>
                </div>
            </div>

            <script>
                // Fetch and display agents
                fetch('/api/agents')
                    .then(response => response.json())
                    .then(data => {
                        const agentList = document.getElementById('agent-list');
                        const agentCount = document.getElementById('agent-count');

                        agentCount.textContent = data.agents.length;

                        if (data.agents.length > 0) {
                            agentList.innerHTML = data.agents.map(agent => `
                                <li class="agent-item">
                                    <div class="agent-name">${agent.name}</div>
                                    <div class="agent-description">${agent.description || 'No description'}</div>
                                </li>
                            `).join('');
                        }
                    })
                    .catch(error => console.error('Error loading agents:', error));

                function runTest() {
                    const input = document.getElementById('test-input').value;
                    const responseDiv = document.getElementById('response');

                    // Here you would send the test to your agents
                    responseDiv.textContent = 'Test functionality coming soon...\\nInput received: ' + input;
                    responseDiv.style.display = 'block';
                }
            </script>
        </body>
        </html>
        """
        return html_content

    @app.get("/api/agents")
    async def list_agents():
        """List all available agents."""
        from .agents import list_agents as get_agent_list, get_agent

        agent_names = get_agent_list()
        agents_data = []

        for name in agent_names:
            agent = get_agent(name)
            if agent:
                agents_data.append({
                    "name": agent.name,
                    "description": agent.description,
                    "model": getattr(agent, 'model', 'unknown')
                })

        return {"agents": agents_data, "count": len(agents_data)}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "ADK Dev UI",
            "agents_loaded": len(app.state.agents)
        }

    @app.post("/api/test")
    async def test_agent(agent_name: str, input_data: Dict[str, Any]):
        """
        Test an agent with given input.

        Args:
            agent_name: Name of the agent to test
            input_data: Input data for the agent

        Returns:
            Agent response
        """
        from .agents import get_agent

        agent = get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        try:
            result = agent.run(input_data)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error testing agent {agent_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    logger.info(f"ADK Dev UI server created for {host}:{port}")
    return app


def create_dev_ui(agents: Optional[List[Any]] = None) -> FastAPI:
    """
    Convenience function to create dev UI server.

    Args:
        agents: List of agents to expose

    Returns:
        FastAPI application
    """
    return get_dev_ui_server(agents=agents)