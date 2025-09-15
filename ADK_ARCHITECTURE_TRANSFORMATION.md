# PresentationPro Architecture Transformation Plan

## Executive Summary

This document outlines the complete transformation of PresentationPro from a monolithic agent deployment to a distributed, protocol-based multi-agent system following Google's InstaVibe patterns and A2A protocol standards.

## Current State Analysis

### Problems Identified
1. **Monolithic Deployment**: All agents in single container (`adkpy`)
2. **Direct Function Calls**: Agents instantiated globally and called directly
3. **No Service Discovery**: Static agent references in `main.py`
4. **Tight Coupling**: Direct imports and dependencies between agents
5. **Mixed Concerns**: Tools and agent logic combined
6. **No Protocol Layer**: Missing A2A communication standards

## Target Architecture

### Core Principles
- **Microservices Pattern**: Each agent as independent service
- **Protocol-Based Communication**: A2A protocol for all agent interactions
- **Dynamic Discovery**: Agent Cards for service registration
- **Tool Separation**: MCP server for external tools
- **Scalability**: Individual agent scaling and deployment

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                    Orchestrator Service                      │
│  - FastAPI REST endpoints                                    │
│  - A2A Client (RemoteAgentConnections)                      │
│  - Agent Discovery (AgentCardResolver)                      │
│  - Session Management                                        │
└──────┬──────────────────────────────────────────┬───────────┘
       │ A2A Protocol                              │ A2A Protocol
┌──────▼───────┐  ┌──────────┐  ┌────────────┐  ┌▼──────────┐
│   Clarifier  │  │ Outline  │  │SlideWriter │  │  Critic   │
│    Agent     │  │  Agent   │  │   Agent    │  │   Agent   │
│  Container   │  │Container │  │ Container  │  │ Container │
└──────────────┘  └──────────┘  └────────────┘  └───────────┘
       │                                                │
       └────────────────┬───────────────────────────────┘
                        │ MCP Protocol
                ┌───────▼────────┐
                │   MCP Server   │
                │  - ArangoDB    │
                │  - WebSearch   │
                │  - Vision      │
                └────────────────┘
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Set up A2A protocol infrastructure
- Create base agent template with A2A server
- Implement MCP server for tools
- Create agent discovery mechanism

### Phase 2: Agent Transformation (Week 2)
- Transform each agent to A2A pattern
- Implement Agent Cards
- Create individual Dockerfiles
- Set up agent executors

### Phase 3: Orchestrator Redesign (Week 3)
- Replace direct calls with A2A clients
- Implement dynamic agent discovery
- Add session and task management
- Create error handling and retries

### Phase 4: Deployment & Testing (Week 4)
- Docker Compose configuration
- Integration testing
- Performance optimization
- Documentation and rollout

## Directory Structure

```
presentationPro/
├── adkpy/
│   ├── agents/
│   │   ├── base/
│   │   │   ├── a2a_base.py          # Base A2A server implementation
│   │   │   ├── agent_base.py        # Base ADK agent
│   │   │   └── executor_base.py     # Base executor
│   │   ├── clarifier/
│   │   │   ├── agent.py             # ADK Agent implementation
│   │   │   ├── a2a_server.py        # A2A protocol server
│   │   │   ├── agent_executor.py    # Custom executor
│   │   │   ├── schemas.py           # Pydantic models
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   ├── outline/
│   │   │   └── (same structure)
│   │   ├── slide_writer/
│   │   ├── critic/
│   │   ├── notes_polisher/
│   │   ├── design/
│   │   ├── script_writer/
│   │   └── research/
│   ├── orchestrator/
│   │   ├── main.py                  # FastAPI app
│   │   ├── a2a_client.py           # A2A client connections
│   │   ├── discovery.py            # Agent discovery
│   │   ├── session_manager.py      # Session management
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── tools/
│   │   ├── mcp_server/
│   │   │   ├── server.py           # MCP server implementation
│   │   │   ├── tools/              # Tool implementations
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   └── shared/                 # Shared tool utilities
│   └── docker-compose.yml
```

## Migration Strategy

### Step 1: Create Base Infrastructure
1. Implement base A2A server class
2. Create agent executor template
3. Set up MCP server wrapper
4. Implement discovery service

### Step 2: Transform One Agent (Clarifier)
1. Create A2A server with Agent Card
2. Implement agent executor
3. Containerize with Dockerfile
4. Test A2A communication

### Step 3: Update Orchestrator
1. Replace direct agent calls
2. Implement A2A client connections
3. Add discovery mechanism
4. Test end-to-end flow

### Step 4: Transform Remaining Agents
1. Apply pattern to all agents
2. Update Docker Compose
3. Test multi-agent flows
4. Optimize performance

## Key Benefits

### Technical Benefits
- **Scalability**: Independent agent scaling
- **Maintainability**: Clear separation of concerns
- **Testability**: Isolated agent testing
- **Flexibility**: Easy agent addition/removal
- **Resilience**: Fault isolation

### Business Benefits
- **Faster Development**: Parallel agent development
- **Cloud Ready**: Compatible with Cloud Run, K8s
- **Cost Optimization**: Scale only what's needed
- **Version Management**: Independent agent versions
- **Team Autonomy**: Teams own individual agents

## Risk Mitigation

### Identified Risks
1. **Complexity Increase**: More moving parts
   - Mitigation: Comprehensive logging and monitoring
2. **Network Latency**: Inter-agent communication
   - Mitigation: Connection pooling, caching
3. **Development Overhead**: More boilerplate
   - Mitigation: Code generation, templates
4. **Debugging Difficulty**: Distributed system
   - Mitigation: Distributed tracing, correlation IDs

## Success Metrics

- **Performance**: < 100ms inter-agent latency
- **Availability**: 99.9% uptime per agent
- **Scalability**: Support 100+ concurrent sessions
- **Development**: 50% reduction in agent development time
- **Deployment**: < 5 minute agent deployment

## Rollout Plan

### Week 1
- Set up development environment
- Create base templates
- Transform Clarifier agent
- Test A2A communication

### Week 2
- Transform remaining agents
- Implement MCP server
- Update orchestrator
- Integration testing

### Week 3
- Docker Compose setup
- Performance testing
- Documentation
- Team training

### Week 4
- Production deployment
- Monitoring setup
- Performance tuning
- Go-live

## Conclusion

This transformation will position PresentationPro as a production-ready, scalable multi-agent system following industry best practices and Google's proven patterns. The investment in proper architecture will pay dividends in maintainability, scalability, and development velocity.