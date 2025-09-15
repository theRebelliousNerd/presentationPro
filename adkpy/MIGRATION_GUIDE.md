# Migration Guide: Monolithic to A2A Architecture

## Overview

This guide provides step-by-step instructions for migrating PresentationPro from the current monolithic architecture to the new A2A protocol-based multi-agent system.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+
- Access to Google Gemini API
- Basic understanding of A2A protocol

## Migration Steps

### Phase 1: Preparation (Day 1)

#### 1.1 Backup Current System
```bash
# Backup current codebase
cp -r adkpy adkpy_backup

# Export current data
docker exec presentationpro-arangodb arangodump \
  --server.database _system \
  --output-directory /backup
```

#### 1.2 Install Dependencies
```bash
# Install A2A libraries
pip install starlette uvicorn httpx google-adk a2a-python

# Install development tools
pip install pytest pytest-asyncio black mypy
```

#### 1.3 Set Up Development Environment
```bash
# Create .env file with required variables
cat > .env << EOF
GOOGLE_GENAI_API_KEY=your_key_here
ARANGO_ROOT_PASSWORD=root
BING_SEARCH_API_KEY=optional_key
EOF
```

### Phase 2: Deploy Base Infrastructure (Day 2)

#### 2.1 Deploy MCP Server
```bash
# Build and start MCP server
cd adkpy/tools/mcp_server
docker build -t presentationpro-mcp-server .
docker run -d --name mcp-server -p 8090:8090 presentationpro-mcp-server
```

#### 2.2 Test MCP Server
```bash
# Test MCP endpoints
curl http://localhost:8090/
curl http://localhost:8090/tools
curl http://localhost:8090/health
```

### Phase 3: Agent Migration (Days 3-5)

#### 3.1 Migrate Clarifier Agent
```bash
# Copy base files
cp -r agents/base agents/clarifier/

# Update agent implementation
# - Replace BaseAgent with A2A server
# - Implement agent executor
# - Create Dockerfile

# Build and test
cd agents/clarifier
docker build -t clarifier-agent .
docker run -d --name clarifier -p 8001:8001 clarifier-agent

# Verify agent card
curl http://localhost:8001/
```

#### 3.2 Migrate Remaining Agents
For each agent (outline, slide_writer, critic, etc.):

1. Create agent directory structure
2. Copy and adapt agent.py
3. Create a2a_server.py
4. Create agent_executor.py
5. Create Dockerfile and requirements.txt
6. Build and test individually

### Phase 4: Deploy Orchestrator (Day 6)

#### 4.1 Build New Orchestrator
```bash
cd adkpy/orchestrator
docker build -t presentationpro-orchestrator .
```

#### 4.2 Start Orchestrator
```bash
docker run -d \
  --name orchestrator \
  -p 8088:8088 \
  --network presentationpro-network \
  -e MCP_SERVER_URL=http://mcp-server:8090 \
  presentationpro-orchestrator
```

#### 4.3 Verify Orchestrator
```bash
# Check health
curl http://localhost:8088/health

# List connected agents
curl http://localhost:8088/v1/agents
```

### Phase 5: Integration Testing (Day 7)

#### 5.1 Run System Tests
```bash
python test_a2a_system.py
```

#### 5.2 Test Frontend Integration
Update frontend to use new endpoints:
- `/v1/clarify` → Same interface
- `/v1/outline` → Same interface
- `/v1/slide/write` → Same interface

### Phase 6: Full Deployment (Day 8)

#### 6.1 Stop Old System
```bash
docker-compose down
```

#### 6.2 Start New System
```bash
cd adkpy
docker-compose up -d
```

#### 6.3 Verify All Services
```bash
docker-compose ps
docker-compose logs -f
```

## Rollback Plan

If issues occur during migration:

### Immediate Rollback
```bash
# Stop new system
cd adkpy
docker-compose down

# Restore old system
cd ..
docker-compose up -d
```

### Data Recovery
```bash
# Restore ArangoDB backup
docker exec presentationpro-arangodb arangorestore \
  --server.database _system \
  --input-directory /backup
```

## Configuration Changes

### Frontend Changes

Update `src/lib/orchestrator.ts`:
```typescript
// Old endpoints remain the same
// Only internal implementation changes
const ADK_BASE_URL = process.env.ADK_BASE_URL || 'http://orchestrator:8088';
```

### Environment Variables

New variables required:
```bash
# Agent-specific models (optional)
CLARIFIER_MODEL=googleai/gemini-2.5-flash
OUTLINE_MODEL=googleai/gemini-2.5-flash
SLIDE_WRITER_MODEL=googleai/gemini-2.5-flash
CRITIC_MODEL=googleai/gemini-2.5-pro
DESIGN_MODEL=googleai/gemini-2.5-flash
NOTES_MODEL=googleai/gemini-2.5-flash

# Service URLs
MCP_SERVER_URL=http://mcp-server:8090
```

## Monitoring and Validation

### Health Checks
```bash
# Check all services
for port in 8088 8001 8002 8003 8004 8005 8006 8007 8008 8090; do
  echo "Checking port $port"
  curl -s http://localhost:$port/health | jq .status
done
```

### Log Monitoring
```bash
# Watch all logs
docker-compose logs -f

# Watch specific agent
docker logs -f presentationpro-clarifier
```

### Performance Testing
```bash
# Run load test
python load_test.py --concurrent=10 --iterations=100
```

## Troubleshooting

### Common Issues

#### 1. Agent Not Connecting
```bash
# Check agent logs
docker logs presentationpro-<agent-name>

# Verify network
docker network inspect presentationpro-network

# Test connectivity
docker exec orchestrator ping clarifier
```

#### 2. MCP Server Issues
```bash
# Check MCP logs
docker logs presentationpro-mcp-server

# Test tool execution
curl -X POST http://localhost:8090/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "web_search", "parameters": {"query": "test"}}'
```

#### 3. Performance Issues
- Check resource usage: `docker stats`
- Scale specific agents: `docker-compose up -d --scale slide-writer=3`
- Enable caching in MCP server

## Post-Migration Tasks

1. **Documentation Update**
   - Update API documentation
   - Create agent-specific READMEs
   - Document new deployment process

2. **Monitoring Setup**
   - Configure Prometheus metrics
   - Set up Grafana dashboards
   - Create alerting rules

3. **CI/CD Pipeline**
   - Update GitHub Actions
   - Add agent-specific tests
   - Configure automated deployments

4. **Team Training**
   - Conduct A2A protocol workshop
   - Review new debugging procedures
   - Share best practices

## Support

For migration support:
- Check logs: `docker-compose logs`
- Run diagnostics: `python diagnose.py`
- Review test results: `cat test_results.json`

## Conclusion

This migration transforms PresentationPro into a scalable, maintainable multi-agent system. The A2A protocol enables:
- Independent agent deployment
- Dynamic service discovery
- Protocol-based communication
- Better fault isolation
- Easier testing and debugging

After successful migration, the system will be ready for production deployment and future enhancements.