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
                    min-height: 140px;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-family: monospace;
                    background: #fbfbfb;
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
                .response, .workflow-status {
                    background: #f0f0f0;
                    padding: 10px;
                    border-radius: 4px;
                    margin-top: 10px;
                    white-space: pre-wrap;
                    font-family: monospace;
                }
                .workflow-trace {
                    margin-top: 12px;
                }
                .trace-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 0.85em;
                }
                .trace-table th, .trace-table td {
                    border: 1px solid #e0e0e0;
                    padding: 6px 8px;
                    text-align: left;
                }
                .trace-table th {
                    background: #f7f7f7;
                }
                .hint {
                    font-size: 0.9em;
                    color: #555;
                    margin-bottom: 8px;
                }
            </style>
        </head>
        <body>
            <h1>ADK Development UI</h1>

            <div class="container">
                <h2>System Status</h2>
                <p>Status: <span class="status">Running</span></p>
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
                <h2>Presentation Workflow Runner</h2>
                <p class="hint">Post to <code>/v1/workflow/presentation</code> and inspect the resulting trace, quality metadata, and final state.</p>
                <textarea id="workflow-input" spellcheck="false">{
  "presentationId": "workflow-demo",
  "history": [],
  "initialInput": {
    "text": "Create a quick overview of our Q4 AI initiatives",
    "audience": "executive",
    "length": "short"
  },
  "newFiles": []
}</textarea>
                <button onclick="runWorkflow()">Run Workflow</button>
                <div id="workflow-status" class="workflow-status"></div>
                <div id="workflow-trace" class="workflow-trace"></div>
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

                    responseDiv.textContent = 'Test functionality coming soon...\nInput received: ' + input;
                    responseDiv.style.display = 'block';
                }

                async function runWorkflow() {
                    const inputEl = document.getElementById('workflow-input');
                    const statusEl = document.getElementById('workflow-status');
                    const traceEl = document.getElementById('workflow-trace');
                    let payload;
                    try {
                        payload = JSON.parse(inputEl.value);
                    } catch (err) {
                        statusEl.textContent = 'Invalid JSON payload';
                        statusEl.style.background = '#fdecea';
                        return;
                    }

                    statusEl.textContent = 'Running workflow...';
                    statusEl.style.background = '#f0f0f0';
                    traceEl.innerHTML = '';

                    try {
                        const res = await fetch('/v1/workflow/presentation', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (!res.ok) {
                            const detail = await res.text();
                            statusEl.textContent = `Request failed (${res.status}): ${detail}`;
                            statusEl.style.background = '#fdecea';
                            return;
                        }
                        const data = await res.json();
                        renderWorkflow(data);
                    } catch (err) {
                        statusEl.textContent = 'Error: ' + err;
                        statusEl.style.background = '#fdecea';
                    }
                }

                function renderWorkflow(data) {
                    const statusEl = document.getElementById('workflow-status');
                    const traceEl = document.getElementById('workflow-trace');
                    const finalStatus = (data.final && data.final.status) || 'complete';
                    statusEl.style.background = finalStatus === 'complete' ? '#e8f5e9' : '#fff8e1';
                    statusEl.textContent = `Session ${data.sessionId || 'n/a'} · Status: ${finalStatus}`;

                    const trace = Array.isArray(data.trace) ? data.trace : [];
                    if (!trace.length) {
                        traceEl.innerHTML = '<p class="hint">No trace entries returned.</p>';
                    } else {
                        let rows = '<table class="trace-table"><thead><tr><th>Step</th><th>Type</th><th>Summary</th></tr></thead><tbody>';
                        trace.forEach((step, idx) => {
                            const keys = step && step.result ? Object.keys(step.result) : [];
                            const summary = keys.length ? keys.slice(0, 4).join(', ') : 'ok';
                            rows += `<tr><td>${step?.id || 'step-' + (idx + 1)}</td><td>${step?.type || 'step'}</td><td>${summary}</td></tr>`;
                        });
                        rows += '</tbody></table>';
                        traceEl.innerHTML = rows;
                    }

                    if (data.state && data.state.metadata && Array.isArray(data.state.metadata.quality) && data.state.metadata.quality.length) {
                        const quality = data.state.metadata.quality;
                        const qualityList = quality.map((entry, idx) => {
                            const missing = (entry.missingCitations || []).length;
                            const violations = (entry.violations || []).length;
                            return `<li>Snapshot ${idx + 1}: ${missing} missing citations, ${violations} violations</li>`;
                        }).join('');
                        const ul = `<div class="hint">Quality snapshots:</div><ul>${qualityList}</ul>`;
                        traceEl.innerHTML += ul;
                    }
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