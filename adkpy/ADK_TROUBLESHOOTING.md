# ADK Troubleshooting Guide

## Table of Contents
1. [Most Common Issues](#most-common-issues)
2. [ADK Dev UI Issues](#adk-dev-ui-issues)
3. [Agent Discovery Problems](#agent-discovery-problems)
4. [Import and Module Errors](#import-and-module-errors)
5. [API and Authentication Issues](#api-and-authentication-issues)
6. [A2A Communication Failures](#a2a-communication-failures)
7. [Performance Issues](#performance-issues)
8. [Deployment Problems](#deployment-problems)
9. [Debugging Techniques](#debugging-techniques)
10. [PresentationPro Specific Issues](#presentationpro-specific-issues)

## Most Common Issues

### Quick Fixes for Top 5 Problems

1. **Dev UI Shows Directory Names Instead of Agents**
   ```bash
   # Solution: Ensure agent.py has root_agent
   # Check: Each agent directory must have agent.py with:
   root_agent = Agent(...)  # or LlmAgent(...)
   ```

2. **Module Import Errors**
   ```bash
   # Solution: Add __init__.py files
   touch agents/__init__.py
   touch agents/clarifier/__init__.py
   ```

3. **API Key Not Found**
   ```bash
   # Solution: Set environment variable
   export GOOGLE_GENAI_API_KEY=your_key_here
   ```

4. **Port Already in Use**
   ```bash
   # Solution: Use different port or kill process
   lsof -i :8100
   kill -9 <PID>
   # Or use different port
   adk web --port 8101
   ```

5. **Agents Not Responding**
   ```bash
   # Solution: Check logs
   docker logs presentationpro-adkpy-1
   # Restart container
   docker compose restart adkpy
   ```

## ADK Dev UI Issues

### Issue: Dev UI Not Starting

**Symptoms:**
- `adk web` command fails
- Error: "command not found"

**Diagnosis:**
```bash
# Check ADK installation
python -c "import google.adk; print(google.adk.__version__)"

# Check PATH
which adk
```

**Solutions:**

1. **Reinstall ADK**:
   ```bash
   pip uninstall google-adk
   pip install google-adk
   ```

2. **Use Python module directly**:
   ```python
   # launch_dev.py
   from google.adk import dev
   dev.run(port=8100)
   ```

3. **Virtual environment issue**:
   ```bash
   # Ensure venv is activated
   source env/bin/activate  # Linux/Mac
   env\Scripts\activate     # Windows

   # Install in venv
   pip install google-adk
   ```

### Issue: Dev UI Blank or Not Loading

**Symptoms:**
- Browser shows blank page
- Console errors in browser

**Diagnosis:**
```bash
# Check browser console (F12)
# Look for JavaScript errors
# Check network tab for failed requests
```

**Solutions:**

1. **Clear browser cache**:
   - Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)

2. **Try different browser**:
   - Chrome/Edge recommended
   - Disable ad blockers

3. **Check firewall/proxy**:
   ```bash
   # Test local connectivity
   curl http://localhost:8100
   ```

## Agent Discovery Problems

### Issue: Agents Not Appearing in Dev UI

**THE MOST CRITICAL ISSUE - COMPLETE SOLUTION**

**Symptoms:**
- Dev UI shows directory names (e.g., "clarifier", "outline")
- No agent cards visible
- Can't interact with agents

**Root Cause:**
ADK scans for `agent.py` files with `root_agent` variable

**Complete Diagnostic Process:**

```bash
# 1. Verify directory structure
tree adkpy/agents -L 2

# Expected output:
# agents/
# ├── clarifier/
# │   ├── agent.py      # MUST exist
# │   └── __init__.py
# ├── outline/
# │   ├── agent.py      # MUST exist
# │   └── __init__.py
# ...

# 2. Check each agent.py file
for dir in agents/*/; do
    echo "Checking $dir"
    if [ -f "${dir}agent.py" ]; then
        grep -n "root_agent" "${dir}agent.py"
    else
        echo "  ERROR: No agent.py found!"
    fi
done

# 3. Validate Python syntax
for file in agents/*/agent.py; do
    echo "Validating $file"
    python -m py_compile "$file"
done
```

**Solution 1: Fix agent.py Structure**

```python
# agents/clarifier/agent.py
from google.adk.agents import Agent

# CRITICAL: Must have root_agent variable
root_agent = Agent(
    name="clarifier_agent",
    model="gemini-2.0-flash",
    description="Refines presentation goals",
    instruction="""You are a clarifier agent..."""
)

# Optional: Additional agents
agents = []  # Can be empty or contain sub-agents
```

**Solution 2: Launch from Correct Directory**

```bash
# ADK looks for agents relative to current directory
cd adkpy/agents  # IMPORTANT: cd into agents directory
adk web --port 8100
```

**Solution 3: Explicit Agent Loading**

```python
# launch_with_agents.py
from google.adk import dev
import sys
import os

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

# Import all agents
from clarifier.agent import root_agent as clarifier
from outline.agent import root_agent as outline
from slide_writer.agent import root_agent as slide_writer

# Run with explicit agents list
dev.run(
    agents=[clarifier, outline, slide_writer],
    port=8100,
    host="127.0.0.1"
)
```

**Solution 4: Debug Agent Discovery**

```python
# debug_discovery.py
import os
from pathlib import Path

def check_agent_discovery():
    """Debug why agents aren't discovered."""

    agents_dir = Path("agents")

    print("Checking agent discovery...")
    print(f"Agents directory: {agents_dir.absolute()}")

    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir():
            print(f"\n{agent_dir.name}:")

            agent_file = agent_dir / "agent.py"
            if agent_file.exists():
                print(f"  ✓ agent.py exists")

                # Check for root_agent
                content = agent_file.read_text()
                if "root_agent" in content:
                    print(f"  ✓ root_agent defined")

                    # Try to import
                    try:
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(
                            f"{agent_dir.name}.agent",
                            agent_file
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        if hasattr(module, 'root_agent'):
                            agent = module.root_agent
                            print(f"  ✓ Successfully imported: {agent.name}")
                        else:
                            print(f"  ✗ root_agent not accessible")
                    except Exception as e:
                        print(f"  ✗ Import error: {e}")
                else:
                    print(f"  ✗ root_agent not defined")
            else:
                print(f"  ✗ agent.py missing")

if __name__ == "__main__":
    check_agent_discovery()
```

### Issue: Agent Import Errors

**Symptoms:**
- `ModuleNotFoundError: No module named 'agents'`
- `ImportError: cannot import name 'root_agent'`

**Solutions:**

1. **Fix Python Path**:
   ```python
   # In agent.py files
   import sys
   import os
   sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
   ```

2. **Add __init__.py files**:
   ```bash
   # Create __init__.py in all directories
   find agents -type d -exec touch {}/__init__.py \;
   ```

3. **Use relative imports**:
   ```python
   # In agents/clarifier/agent.py
   from ..common.base import BaseAgent  # Relative import
   ```

## Import and Module Errors

### Issue: Circular Import Dependencies

**Symptoms:**
- `ImportError: cannot import name X from partially initialized module`

**Solution:**
```python
# Avoid circular imports by:
# 1. Import inside functions
def create_agent():
    from other_module import SomeClass  # Import when needed
    return SomeClass()

# 2. Use TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from other_module import SomeClass

# 3. Restructure modules
# Move shared code to common module
```

### Issue: Package Version Conflicts

**Diagnosis:**
```bash
# Check installed versions
pip list | grep google

# Check for conflicts
pip check
```

**Solution:**
```bash
# Create clean environment
python -m venv fresh_env
source fresh_env/bin/activate

# Install exact versions
pip install google-adk==1.0.0
pip install google-generativeai==0.3.2
```

## API and Authentication Issues

### Issue: API Key Not Working

**Symptoms:**
- `401 Unauthorized` errors
- "API key not valid" messages

**Diagnosis:**
```python
# Test API key
import google.generativeai as genai

genai.configure(api_key="your-key")
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Test")
    print("API key is valid")
except Exception as e:
    print(f"API key error: {e}")
```

**Solutions:**

1. **Check key format**:
   ```bash
   # Key should start with "AIza"
   echo $GOOGLE_GENAI_API_KEY | head -c 4
   ```

2. **Verify key permissions**:
   - Go to Google AI Studio
   - Check key is enabled for Gemini API

3. **Use .env file**:
   ```python
   # .env
   GOOGLE_GENAI_API_KEY=your_key_here

   # In Python
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Issue: Rate Limiting

**Symptoms:**
- `429 Too Many Requests`
- Intermittent failures

**Solution:**
```python
# Implement exponential backoff
import time
from typing import Any

def retry_with_backoff(func, max_retries=3):
    """Retry with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

## A2A Communication Failures

### Issue: Agents Can't Connect

**Symptoms:**
- `Connection refused` errors
- Timeout errors

**Diagnosis:**
```bash
# Check if agents are running
netstat -tlnp | grep -E "(10001|10002|10003)"

# Test connectivity
curl http://localhost:10001/health
```

**Solutions:**

1. **Start agents in correct order**:
   ```bash
   # Start in dependency order
   python agents/research/a2a_server.py &
   python agents/clarifier/a2a_server.py &
   python agents/outline/a2a_server.py &
   # Wait for all to start
   sleep 5
   python agents/orchestrator/a2a_server.py
   ```

2. **Use Docker Compose**:
   ```yaml
   # docker-compose.yml
   services:
     clarifier:
       depends_on:
         - research
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:10001/health"]
         interval: 5s
         retries: 5
   ```

### Issue: Message Format Errors

**Symptoms:**
- `422 Unprocessable Entity`
- Schema validation errors

**Solution:**
```python
# Validate messages before sending
from pydantic import ValidationError

def validate_message(message: dict, schema: dict):
    """Validate message against schema."""
    try:
        # Use pydantic or jsonschema
        from jsonschema import validate
        validate(instance=message, schema=schema)
        return True
    except ValidationError as e:
        print(f"Validation error: {e}")
        return False
```

## Performance Issues

### Issue: Slow Agent Response

**Diagnosis:**
```python
# Profile agent performance
import cProfile
import pstats

def profile_agent():
    profiler = cProfile.Profile()
    profiler.enable()

    # Run agent
    result = agent.run(input_data)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

**Solutions:**

1. **Optimize prompts**:
   ```python
   # Reduce token usage
   instruction = """Be concise. Respond with JSON only."""
   ```

2. **Implement caching**:
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def cached_llm_call(prompt_hash):
       return llm.generate(prompt)
   ```

3. **Use async operations**:
   ```python
   # Parallel processing
   async def process_parallel(items):
       tasks = [process_item(item) for item in items]
       return await asyncio.gather(*tasks)
   ```

### Issue: High Memory Usage

**Diagnosis:**
```bash
# Monitor memory
top -p $(pgrep -f agent.py)

# Python memory profiling
python -m memory_profiler agent.py
```

**Solutions:**

1. **Clear unused objects**:
   ```python
   import gc

   # Force garbage collection
   gc.collect()

   # Clear large objects
   del large_data
   ```

2. **Stream responses**:
   ```python
   # Don't accumulate entire response
   async for chunk in stream_response():
       process_chunk(chunk)
       # Don't store all chunks
   ```

## Deployment Problems

### Issue: Docker Container Crashes

**Diagnosis:**
```bash
# Check logs
docker logs presentationpro-adkpy-1 --tail 50

# Check exit code
docker inspect presentationpro-adkpy-1 --format='{{.State.ExitCode}}'
```

**Solutions:**

1. **Add health checks**:
   ```dockerfile
   # Dockerfile
   HEALTHCHECK --interval=30s --timeout=3s \
     CMD python -c "import requests; requests.get('http://localhost:8088/health')"
   ```

2. **Increase resources**:
   ```yaml
   # docker-compose.yml
   services:
     adkpy:
       mem_limit: 2g
       cpus: '1.0'
   ```

### Issue: Cloud Run Deployment Fails

**Symptoms:**
- Build succeeds but deployment fails
- "Container failed to start"

**Solution:**
```dockerfile
# Ensure proper Cloud Run configuration
FROM python:3.10-slim

# Cloud Run expects PORT env var
ENV PORT 8080
EXPOSE 8080

# Use non-root user
RUN useradd -m appuser
USER appuser

# Start command
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
```

## Debugging Techniques

### Enable Detailed Logging

```python
# Enable ADK debug logging
import logging

# Set all loggers to DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ADK specific loggers
logging.getLogger('google.adk').setLevel(logging.DEBUG)
logging.getLogger('google.adk.agents').setLevel(logging.DEBUG)
```

### Trace Agent Execution

```python
# trace_agent.py
import sys
import trace

# Create tracer
tracer = trace.Trace(
    count=False,
    trace=True,
    tracedirs=[sys.prefix, sys.exec_prefix]
)

# Trace agent execution
tracer.run('agent.run(input_data)')
```

### Interactive Debugging

```python
# Add breakpoints
import pdb

def process_request(request):
    # Set breakpoint
    pdb.set_trace()

    # Or use built-in breakpoint (Python 3.7+)
    breakpoint()

    result = agent.run(request)
    return result
```

### Network Debugging

```bash
# Monitor HTTP traffic
tcpdump -i lo -A 'tcp port 10001'

# Use mitmproxy for HTTP debugging
mitmdump -p 8888 --mode reverse:http://localhost:10001
```

## PresentationPro Specific Issues

### Issue: Outline Not Generating Properly

**Symptoms:**
- Empty sections
- Missing slide structure

**Diagnosis:**
```python
# Check outline agent response
def debug_outline_agent():
    from agents.outline.agent import root_agent

    test_input = {
        "clarified_goals": {
            "topic": "AI Safety",
            "audience": "executives",
            "duration": 20
        }
    }

    result = root_agent.run(test_input)
    print(json.dumps(result, indent=2))

    # Validate structure
    assert "title" in result
    assert "sections" in result
    assert len(result["sections"]) > 0
```

**Solution:**
```python
# Fix outline agent prompt
instruction = """
Generate a presentation outline with the following structure:
{
    "title": "string",
    "sections": [
        {
            "title": "string",
            "points": ["string"],
            "duration_minutes": number
        }
    ],
    "total_slides": number
}

Ensure each section has at least 2 points.
"""
```

### Issue: Images Not Generating

**Symptoms:**
- Visual suggestions present but no images
- Image generation timeouts

**Solution:**
```python
# Implement fallback for image generation
async def generate_image_with_fallback(prompt: str):
    try:
        # Try primary service
        return await generate_with_dalle(prompt)
    except Exception as e:
        logger.warning(f"DALL-E failed: {e}")

        try:
            # Fallback to Stability AI
            return await generate_with_stability(prompt)
        except Exception as e2:
            logger.error(f"All image services failed: {e2}")
            # Return placeholder
            return "placeholder_image.png"
```

### Issue: Token Limits Exceeded

**Symptoms:**
- Truncated responses
- "Maximum context length exceeded"

**Solution:**
```python
# Implement sliding window for long content
def process_long_content(content: str, max_tokens: int = 4000):
    """Process content in chunks."""
    chunks = split_into_chunks(content, max_tokens)
    results = []

    for i, chunk in enumerate(chunks):
        # Include overlap for context
        if i > 0:
            overlap = chunks[i-1][-500:]  # Last 500 chars
            chunk = overlap + chunk

        result = process_chunk(chunk)
        results.append(result)

    return merge_results(results)
```

### Issue: A2A Orchestration Hanging

**Symptoms:**
- Orchestrator waits indefinitely
- No error messages

**Solution:**
```python
# Add timeouts to all A2A calls
async def call_agent_with_timeout(
    client: A2AClient,
    message: dict,
    timeout: int = 30
):
    """Call agent with timeout."""
    try:
        return await asyncio.wait_for(
            client.send_message(message),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Agent call timed out after {timeout}s")
        # Return default response
        return {"status": "timeout", "result": {}}
```

## Recovery Procedures

### Complete System Reset

```bash
#!/bin/bash
# reset_system.sh

echo "Resetting PresentationPro ADK System..."

# 1. Stop all services
docker compose down
pkill -f "python.*agent"

# 2. Clear caches
rm -rf .cache/
rm -rf __pycache__/
find . -type d -name "__pycache__" -exec rm -rf {} +

# 3. Reset database
docker volume rm presentationpro_arangodb_data

# 4. Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# 5. Restart services
docker compose up -d

echo "System reset complete"
```

### Emergency Diagnostics

```python
# emergency_diagnostic.py
"""
Run this when nothing else works.
"""

import sys
import os
import subprocess
import json

def run_diagnostics():
    """Run complete system diagnostics."""

    results = {
        "python_version": sys.version,
        "pip_packages": [],
        "environment_vars": {},
        "agent_status": {},
        "port_status": {},
        "docker_status": {}
    }

    # Check Python packages
    pip_list = subprocess.run(
        ["pip", "list", "--format=json"],
        capture_output=True,
        text=True
    )
    results["pip_packages"] = json.loads(pip_list.stdout)

    # Check environment
    for key in ["GOOGLE_GENAI_API_KEY", "PYTHONPATH", "PORT"]:
        results["environment_vars"][key] = os.environ.get(key, "NOT SET")

    # Check ports
    for port in [8100, 10001, 10002, 10003]:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            results["port_status"][port] = "OPEN" if result == 0 else "CLOSED"
            sock.close()
        except:
            results["port_status"][port] = "ERROR"

    # Check Docker
    try:
        docker_ps = subprocess.run(
            ["docker", "ps", "--format", "json"],
            capture_output=True,
            text=True
        )
        results["docker_status"]["running"] = docker_ps.stdout
    except:
        results["docker_status"]["error"] = "Docker not available"

    # Save results
    with open("diagnostic_report.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Diagnostic report saved to diagnostic_report.json")
    return results

if __name__ == "__main__":
    run_diagnostics()
```

## Getting Help

### Resources

1. **Official Documentation**
   - [Google ADK Docs](https://cloud.google.com/adk/docs)
   - [Gemini API Docs](https://ai.google.dev/)

2. **Community Support**
   - Stack Overflow: Tag `google-adk`
   - GitHub Issues: google/adk repository

3. **Logging for Support**
   ```bash
   # Collect logs for support ticket
   ./collect_logs.sh > support_logs.txt
   ```

### Support Checklist

Before requesting help, collect:

- [ ] Error messages and stack traces
- [ ] ADK version (`pip show google-adk`)
- [ ] Python version (`python --version`)
- [ ] Directory structure (`tree agents -L 2`)
- [ ] Sample agent.py file
- [ ] Environment variables (sanitized)
- [ ] Diagnostic report (from script above)