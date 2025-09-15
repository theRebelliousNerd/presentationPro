"""
ADK Dev UI Server

Provides a development interface for testing and debugging agents.
Includes WebSocket support for real-time communication and telemetry.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import asyncio
import time
import uuid
import logging
from pathlib import Path

from . import get_agent, get_all_agents, discover_agents

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Request model for chat interactions."""
    agent_id: str
    message: str
    context: Optional[Dict[str, Any]] = {}
    trace_enabled: bool = True


class ChatResponse(BaseModel):
    """Response model for chat interactions."""
    agent_id: str
    response: Any
    usage: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    timestamp: float


class ActiveSession:
    """Represents an active Dev UI session."""

    def __init__(self, session_id: str, agent_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.agent_id = agent_id
        self.websocket = websocket
        self.conversation_history = []
        self.created_at = time.time()
        self.last_activity = time.time()


class DevUIServer:
    """
    Development UI server for ADK agents.
    Provides web interface and WebSocket API for agent interaction.
    """

    def __init__(self, app: FastAPI = None):
        self.app = app or FastAPI()
        self.sessions: Dict[str, ActiveSession] = {}
        self.setup_routes()
        self.setup_websocket()
        self.setup_templates()

    def setup_templates(self):
        """Set up Jinja2 templates for the UI."""
        # Create templates directory if it doesn't exist
        templates_dir = Path(__file__).parent.parent / "dev_ui" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        # Create a basic index.html template
        index_template = templates_dir / "index.html"
        if not index_template.exists():
            index_template.write_text(self.get_default_template())

        self.templates = Jinja2Templates(directory=str(templates_dir))

    def get_default_template(self) -> str:
        """Get the default HTML template for the Dev UI."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ADK Dev UI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: #192940; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .header h1 { font-size: 24px; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .main-grid { display: grid; grid-template-columns: 300px 1fr 350px; gap: 20px; }
        .agent-list { background: white; border-radius: 8px; padding: 20px; height: fit-content; }
        .agent-card { padding: 12px; margin-bottom: 10px; border: 1px solid #e0e0e0; border-radius: 6px; cursor: pointer; transition: all 0.3s; }
        .agent-card:hover { background: #f8f9fa; border-color: #73BF50; }
        .agent-card.active { background: #e8f5e9; border-color: #73BF50; }
        .agent-name { font-weight: 600; color: #192940; }
        .agent-version { font-size: 12px; color: #666; }
        .agent-description { font-size: 13px; color: #555; margin-top: 4px; }
        .chat-container { background: white; border-radius: 8px; display: flex; flex-direction: column; height: 600px; }
        .chat-header { padding: 15px 20px; border-bottom: 1px solid #e0e0e0; }
        .chat-messages { flex: 1; overflow-y: auto; padding: 20px; }
        .message { margin-bottom: 15px; }
        .message.user { text-align: right; }
        .message.agent { text-align: left; }
        .message-bubble { display: inline-block; max-width: 70%; padding: 10px 15px; border-radius: 12px; }
        .user .message-bubble { background: #73BF50; color: white; }
        .agent .message-bubble { background: #f0f0f0; color: #333; }
        .chat-input { padding: 15px 20px; border-top: 1px solid #e0e0e0; }
        .input-group { display: flex; gap: 10px; }
        .input-group input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
        .input-group button { padding: 10px 20px; background: #73BF50; color: white; border: none; border-radius: 6px; cursor: pointer; }
        .input-group button:hover { background: #5ca23e; }
        .telemetry { background: white; border-radius: 8px; padding: 20px; }
        .telemetry h3 { margin-bottom: 15px; color: #192940; }
        .metric { padding: 10px; margin-bottom: 10px; background: #f8f9fa; border-radius: 6px; }
        .metric-label { font-size: 12px; color: #666; }
        .metric-value { font-size: 20px; font-weight: 600; color: #192940; }
        .trace-log { background: #f8f9fa; padding: 10px; border-radius: 6px; margin-top: 15px; max-height: 200px; overflow-y: auto; }
        .trace-entry { font-family: monospace; font-size: 12px; margin-bottom: 5px; }
        .status-indicator { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 5px; }
        .status-indicator.ready { background: #4caf50; }
        .status-indicator.busy { background: #ff9800; }
        .status-indicator.error { background: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ADK Development UI</h1>
            <p>Test and debug your agents in real-time</p>
        </div>

        <div class="main-grid">
            <div class="agent-list">
                <h3>Available Agents</h3>
                <div id="agentList"></div>
            </div>

            <div class="chat-container">
                <div class="chat-header">
                    <h3 id="chatAgentName">Select an agent to start</h3>
                    <div id="chatStatus"></div>
                </div>
                <div class="chat-messages" id="chatMessages"></div>
                <div class="chat-input">
                    <div class="input-group">
                        <input type="text" id="messageInput" placeholder="Type your message..." disabled>
                        <button id="sendButton" disabled>Send</button>
                    </div>
                </div>
            </div>

            <div class="telemetry">
                <h3>Telemetry</h3>
                <div class="metric">
                    <div class="metric-label">Total Tokens</div>
                    <div class="metric-value" id="totalTokens">0</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Response Time</div>
                    <div class="metric-value" id="responseTime">0ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Active Model</div>
                    <div class="metric-value" id="activeModel">-</div>
                </div>
                <div class="trace-log" id="traceLog">
                    <div class="trace-entry">Waiting for activity...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let currentAgent = null;
        let sessionId = null;

        // Load agents on page load
        fetch('/adk-dev/api/agents')
            .then(res => res.json())
            .then(agents => {
                const agentList = document.getElementById('agentList');
                agents.forEach(agent => {
                    const card = document.createElement('div');
                    card.className = 'agent-card';
                    card.innerHTML = `
                        <span class="status-indicator ready"></span>
                        <div class="agent-name">${agent.name}</div>
                        <div class="agent-version">v${agent.version}</div>
                        <div class="agent-description">${agent.description}</div>
                    `;
                    card.onclick = () => selectAgent(agent);
                    agentList.appendChild(card);
                });
            });

        function selectAgent(agent) {
            currentAgent = agent;
            sessionId = generateUUID();

            // Update UI
            document.getElementById('chatAgentName').textContent = agent.name;
            document.getElementById('messageInput').disabled = false;
            document.getElementById('sendButton').disabled = false;
            document.getElementById('chatMessages').innerHTML = '';

            // Update agent cards
            document.querySelectorAll('.agent-card').forEach(card => {
                card.classList.remove('active');
                if (card.querySelector('.agent-name').textContent === agent.name) {
                    card.classList.add('active');
                }
            });

            // Connect WebSocket
            connectWebSocket();
        }

        function connectWebSocket() {
            if (ws) ws.close();

            ws = new WebSocket(`ws://localhost:8089/adk-dev/ws/agent/${currentAgent.name}?session_id=${sessionId}`);

            ws.onopen = () => {
                addSystemMessage('Connected to ' + currentAgent.name);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            ws.onerror = (error) => {
                addSystemMessage('Error: Connection failed');
            };

            ws.onclose = () => {
                addSystemMessage('Disconnected');
            };
        }

        function handleWebSocketMessage(data) {
            if (data.type === 'response') {
                addMessage(data.content, 'agent');
                updateTelemetry(data);
            } else if (data.type === 'event') {
                addTraceEntry(data.content);
            } else if (data.type === 'error') {
                addSystemMessage('Error: ' + data.content);
            }
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message || !ws) return;

            addMessage(message, 'user');

            ws.send(JSON.stringify({
                type: 'request',
                agent_id: currentAgent.name,
                message: message,
                trace_enabled: true
            }));

            input.value = '';
        }

        function addMessage(text, sender) {
            const messages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender;
            messageDiv.innerHTML = `<div class="message-bubble">${text}</div>`;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }

        function addSystemMessage(text) {
            const messages = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.style.textAlign = 'center';
            messageDiv.style.color = '#666';
            messageDiv.style.fontSize = '12px';
            messageDiv.style.margin = '10px 0';
            messageDiv.textContent = text;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }

        function updateTelemetry(data) {
            if (data.usage) {
                const totalTokens = (data.usage.promptTokens || 0) + (data.usage.completionTokens || 0);
                document.getElementById('totalTokens').textContent = totalTokens;
                document.getElementById('activeModel').textContent = data.usage.model || '-';
            }
            if (data.duration) {
                document.getElementById('responseTime').textContent = data.duration + 'ms';
            }
        }

        function addTraceEntry(text) {
            const traceLog = document.getElementById('traceLog');
            const entry = document.createElement('div');
            entry.className = 'trace-entry';
            entry.textContent = new Date().toLocaleTimeString() + ' - ' + text;
            traceLog.appendChild(entry);
            traceLog.scrollTop = traceLog.scrollHeight;
        }

        function generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }

        // Handle Enter key in input
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        document.getElementById('sendButton').onclick = sendMessage;
    </script>
</body>
</html>'''

    def setup_routes(self):
        """Set up HTTP routes for the Dev UI."""

        @self.app.get("/adk-dev", response_class=HTMLResponse)
        async def dev_ui_home(request: Request):
            """Serve the main Dev UI page."""
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.get("/adk-dev/api/agents")
        async def list_agents():
            """API endpoint to list all registered agents."""
            return discover_agents()

        @self.app.get("/adk-dev/api/agent/{agent_id}")
        async def get_agent_details(agent_id: str):
            """Get detailed information about a specific agent."""
            agent = get_agent(agent_id)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
            return agent.get_metadata()

        @self.app.post("/adk-dev/api/agent/{agent_id}/chat")
        async def chat_with_agent(agent_id: str, request: ChatRequest):
            """HTTP endpoint for single chat interaction."""
            agent = get_agent(agent_id)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

            try:
                # Get agent instance
                agent_instance = agent.get_instance()

                # Prepare input based on agent's expected format
                input_data = self.prepare_agent_input(agent_instance, request.message, request.context)

                # Run the agent
                result = agent_instance.run(input_data)

                # Format response
                response = ChatResponse(
                    agent_id=agent_id,
                    response=result.data,
                    usage=result.usage.model_dump() if hasattr(result, 'usage') else None,
                    trace_id=str(uuid.uuid4()),
                    timestamp=time.time()
                )

                return response

            except Exception as e:
                logger.error(f"Error in chat with agent {agent_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def setup_websocket(self):
        """Set up WebSocket endpoints for real-time communication."""

        @self.app.websocket("/adk-dev/ws/agent/{agent_id}")
        async def websocket_endpoint(websocket: WebSocket, agent_id: str, session_id: str = None):
            """WebSocket endpoint for real-time agent interaction."""
            await websocket.accept()

            # Create session
            session_id = session_id or str(uuid.uuid4())
            session = ActiveSession(session_id, agent_id, websocket)
            self.sessions[session_id] = session

            try:
                while True:
                    # Receive message
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    # Process message
                    await self.handle_websocket_message(session, message)

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "content": str(e)
                })
            finally:
                # Clean up session
                if session_id in self.sessions:
                    del self.sessions[session_id]

    async def handle_websocket_message(self, session: ActiveSession, message: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        message_type = message.get("type")

        if message_type == "request":
            # Process chat request
            await self.process_chat_request(session, message)
        elif message_type == "ping":
            # Respond to ping
            await session.websocket.send_json({"type": "pong"})
        else:
            await session.websocket.send_json({
                "type": "error",
                "content": f"Unknown message type: {message_type}"
            })

    async def process_chat_request(self, session: ActiveSession, message: Dict[str, Any]):
        """Process a chat request via WebSocket."""
        agent_id = session.agent_id
        user_message = message.get("message", "")
        trace_enabled = message.get("trace_enabled", True)

        # Get agent
        agent = get_agent(agent_id)
        if not agent:
            await session.websocket.send_json({
                "type": "error",
                "content": f"Agent {agent_id} not found"
            })
            return

        try:
            # Send trace event
            if trace_enabled:
                await session.websocket.send_json({
                    "type": "event",
                    "content": f"Processing message with {agent_id}"
                })

            # Get agent instance
            agent_instance = agent.get_instance()

            # Prepare input
            input_data = self.prepare_agent_input(
                agent_instance,
                user_message,
                {"history": session.conversation_history}
            )

            # Run agent
            start_time = time.time()
            result = agent_instance.run(input_data)
            duration_ms = int((time.time() - start_time) * 1000)

            # Update conversation history
            session.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            session.conversation_history.append({
                "role": "assistant",
                "content": result.data
            })

            # Send response
            await session.websocket.send_json({
                "type": "response",
                "content": json.dumps(result.data) if not isinstance(result.data, str) else result.data,
                "usage": result.usage.model_dump() if hasattr(result, 'usage') else None,
                "duration": duration_ms,
                "trace_id": str(uuid.uuid4())
            })

            # Send completion event
            if trace_enabled:
                await session.websocket.send_json({
                    "type": "event",
                    "content": f"Completed in {duration_ms}ms"
                })

        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            await session.websocket.send_json({
                "type": "error",
                "content": str(e)
            })

    def prepare_agent_input(self, agent_instance, message: str, context: Dict[str, Any]):
        """Prepare input data for an agent based on its expected format."""
        # This is a simplified version - you'd want to match the actual agent's Input model
        agent_module = agent_instance.__class__.__module__

        # Import the agent's module to get its Input class
        import importlib
        module = importlib.import_module(agent_module)

        if hasattr(module, 'Input'):
            Input = module.Input
            # Try to construct the input based on the Input model
            if 'history' in Input.model_fields:
                return Input(
                    history=context.get('history', []),
                    initialInput={'text': message}
                )
            elif 'text' in Input.model_fields:
                return Input(text=message)
            elif 'query' in Input.model_fields:
                return Input(query=message)

        # Fallback to a generic dict
        return {"message": message, "context": context}


# Create a singleton instance
dev_ui_server = None


def get_dev_ui_server(app: FastAPI = None) -> DevUIServer:
    """Get or create the Dev UI server instance."""
    global dev_ui_server
    if dev_ui_server is None:
        dev_ui_server = DevUIServer(app)
    return dev_ui_server