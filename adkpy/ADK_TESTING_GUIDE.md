# ADK Testing and Evaluation Guide

## Table of Contents
1. [Overview](#overview)
2. [Testing in ADK Dev UI](#testing-in-adk-dev-ui)
3. [Evaluation Framework](#evaluation-framework)
4. [Unit Testing Agents](#unit-testing-agents)
5. [Integration Testing](#integration-testing)
6. [Performance Testing](#performance-testing)
7. [Testing Multi-Agent Workflows](#testing-multi-agent-workflows)
8. [PresentationPro Testing Strategy](#presentationpro-testing-strategy)
9. [Automated Testing Pipeline](#automated-testing-pipeline)
10. [Best Practices](#best-practices)

## Overview

Testing ADK agents involves multiple layers:
- **Interactive Testing**: Using ADK Dev UI for manual testing
- **Evaluation**: Automated scoring of agent outputs
- **Unit Testing**: Testing individual agent components
- **Integration Testing**: Testing agent interactions
- **Performance Testing**: Load and latency testing

## Testing in ADK Dev UI

### Basic Interactive Testing

1. **Launch Dev UI**:
```bash
cd adkpy/agents
adk web --port 8100
```

2. **Select Agent**: Choose agent from the left panel
3. **Enter Input**: Provide test input in the text area
4. **Execute**: Click "Run" to execute agent
5. **Review Output**: Examine response, timing, and token usage

### Testing with Custom Inputs

```python
# test_inputs.py
TEST_CASES = {
    "clarifier": [
        {
            "input": "Create a presentation",
            "expected_keys": ["questions", "understanding_level"]
        },
        {
            "input": "I need a 10-slide presentation about AI safety for executives",
            "expected_keys": ["questions", "understanding_level"],
            "min_understanding": 0.7
        }
    ],
    "outline": [
        {
            "input": {
                "topic": "Renewable Energy",
                "audience": "High school students",
                "duration": 15
            },
            "expected_keys": ["title", "sections", "estimated_slides"]
        }
    ]
}
```

### Batch Testing in Dev UI

```python
# batch_test_dev_ui.py
from google.adk import dev
from agents.clarifier.agent import root_agent as clarifier
import json

def run_batch_tests():
    """Run batch tests through Dev UI."""

    # Load test cases
    with open("test_cases.json") as f:
        test_cases = json.load(f)

    # Run tests for each agent
    results = {}
    for test in test_cases:
        response = dev.test_agent(
            agent=clarifier,
            input_data=test["input"],
            timeout=30
        )
        results[test["id"]] = response

    return results
```

## Evaluation Framework

### Creating Evaluations

```python
# evaluations/clarifier_eval.py
from google.adk.agents import Agent, Evaluation
from typing import Dict, Any, List

class ClarifierEvaluation(Evaluation):
    """Evaluation for clarifier agent."""

    def __init__(self):
        super().__init__(
            name="clarifier_quality_eval",
            description="Evaluates quality of clarification questions"
        )

    def evaluate(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ) -> float:
        """Score the agent output (0.0 to 1.0)."""
        score = 0.0

        # Check for required fields
        if "questions" in output_data:
            score += 0.3

            # Check question quality
            questions = output_data["questions"]
            if len(questions) >= 3:
                score += 0.2
            if all(q.endswith("?") for q in questions):
                score += 0.1

        # Check understanding level
        if "understanding_level" in output_data:
            score += 0.2
            level = output_data["understanding_level"]
            if 0 <= level <= 1:
                score += 0.2

        return min(score, 1.0)

# Register evaluation
clarifier_eval = ClarifierEvaluation()
```

### Running Evaluations

```python
# run_evaluations.py
from google.adk import dev
from google.adk.agents import Agent
from evaluations.clarifier_eval import clarifier_eval
import json

def run_agent_evaluation(
    agent: Agent,
    test_cases: List[Dict],
    evaluation: Evaluation
) -> Dict[str, Any]:
    """Run evaluation on an agent."""

    results = {
        "agent": agent.name,
        "total_tests": len(test_cases),
        "scores": [],
        "average_score": 0
    }

    for test in test_cases:
        # Run agent
        output = agent.run(test["input"])

        # Evaluate output
        score = evaluation.evaluate(test["input"], output)

        results["scores"].append({
            "test_id": test["id"],
            "score": score,
            "input": test["input"],
            "output": output
        })

    # Calculate average
    if results["scores"]:
        results["average_score"] = sum(
            s["score"] for s in results["scores"]
        ) / len(results["scores"])

    return results

# Example usage
if __name__ == "__main__":
    from agents.clarifier.agent import root_agent

    test_cases = [
        {"id": "test_1", "input": "Create a presentation"},
        {"id": "test_2", "input": "AI safety presentation for executives"}
    ]

    results = run_agent_evaluation(
        agent=root_agent,
        test_cases=test_cases,
        evaluation=clarifier_eval
    )

    print(json.dumps(results, indent=2))
```

### Advanced Evaluation with LLM Judge

```python
# evaluations/llm_judge.py
from google.adk.agents import Agent
import google.generativeai as genai

class LLMJudgeEvaluation:
    """Use an LLM to evaluate agent outputs."""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        self.model = genai.GenerativeModel(model_name)

    def evaluate(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        criteria: List[str]
    ) -> Dict[str, Any]:
        """Evaluate output using LLM judge."""

        prompt = f"""
        Evaluate the following agent output based on these criteria:
        {json.dumps(criteria, indent=2)}

        Agent: {agent_name}
        Input: {json.dumps(input_data, indent=2)}
        Output: {json.dumps(output_data, indent=2)}

        Provide scores (0-10) for each criterion and an overall score.
        Return as JSON with format:
        {{
            "criteria_scores": {{"criterion": score}},
            "overall_score": float,
            "feedback": "string"
        }}
        """

        response = self.model.generate_content(prompt)
        return json.loads(response.text)

# Usage
judge = LLMJudgeEvaluation()
evaluation = judge.evaluate(
    agent_name="slide_writer",
    input_data={"outline": {...}},
    output_data={"slides": [...]},
    criteria=[
        "Content relevance",
        "Clarity and structure",
        "Engagement level",
        "Technical accuracy"
    ]
)
```

## Unit Testing Agents

### Basic Agent Unit Tests

```python
# tests/test_clarifier_agent.py
import pytest
from unittest.mock import Mock, patch
from agents.clarifier.agent import ClarifierADKAgent

class TestClarifierAgent:
    """Unit tests for clarifier agent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        mock_llm = Mock()
        return ClarifierADKAgent(
            llm=mock_llm,
            name="test_clarifier",
            description="Test agent"
        )

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "test_clarifier"
        assert agent.description == "Test agent"
        assert agent.instruction is not None

    def test_process_input(self, agent):
        """Test input processing."""
        input_data = {
            "user_request": "Create a presentation about AI"
        }

        # Mock LLM response
        agent.llm.generate.return_value = {
            "questions": [
                "What is your target audience?",
                "How long should the presentation be?",
                "What key topics should be covered?"
            ],
            "understanding_level": 0.6
        }

        result = agent.process(input_data)

        assert "questions" in result
        assert len(result["questions"]) == 3
        assert result["understanding_level"] == 0.6

    @patch('agents.clarifier.agent.validate_input')
    def test_input_validation(self, mock_validate, agent):
        """Test input validation."""
        mock_validate.return_value = True

        valid_input = {"user_request": "Valid request"}
        assert agent.validate_input(valid_input) == True

        mock_validate.return_value = False
        invalid_input = {}
        assert agent.validate_input(invalid_input) == False

    def test_error_handling(self, agent):
        """Test error handling."""
        agent.llm.generate.side_effect = Exception("LLM Error")

        input_data = {"user_request": "Test"}

        with pytest.raises(Exception) as exc_info:
            agent.process(input_data)

        assert "LLM Error" in str(exc_info.value)
```

### Testing Agent Tools

```python
# tests/test_agent_tools.py
import pytest
from unittest.mock import Mock, patch
from tools.presentation_tools import (
    extract_text_from_pdf,
    search_web,
    analyze_image
)

class TestPresentationTools:
    """Test presentation-specific tools."""

    @patch('tools.presentation_tools.fitz')
    def test_pdf_extraction(self, mock_fitz):
        """Test PDF text extraction."""
        # Mock PDF document
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Sample PDF text"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc

        result = extract_text_from_pdf("test.pdf")
        assert "Sample PDF text" in result

    @patch('tools.presentation_tools.requests')
    def test_web_search(self, mock_requests):
        """Test web search functionality."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {"title": "Result 1", "url": "http://example.com"}
            ]
        }
        mock_requests.get.return_value = mock_response

        results = search_web("test query")
        assert len(results) > 0
        assert results[0]["title"] == "Result 1"

    @patch('tools.presentation_tools.Image')
    def test_image_analysis(self, mock_image):
        """Test image analysis."""
        mock_img = Mock()
        mock_img.size = (1920, 1080)
        mock_img.mode = "RGB"
        mock_image.open.return_value = mock_img

        analysis = analyze_image("test.jpg")
        assert analysis["width"] == 1920
        assert analysis["height"] == 1080
        assert analysis["mode"] == "RGB"
```

## Integration Testing

### Testing Agent Chains

```python
# tests/test_agent_integration.py
import pytest
import asyncio
from agents.orchestrator.orchestrator_agent import PresentationOrchestrator

class TestAgentIntegration:
    """Integration tests for agent workflows."""

    @pytest.fixture
    async def orchestrator(self):
        """Create orchestrator instance."""
        orch = PresentationOrchestrator()
        yield orch
        await orch.cleanup()

    @pytest.mark.asyncio
    async def test_clarifier_to_outline_flow(self, orchestrator):
        """Test clarifier -> outline agent flow."""

        # Initial request
        state = {
            "user_request": "Create a presentation about renewable energy"
        }

        # Run clarification
        clarified = await orchestrator._clarify_request(
            state["user_request"]
        )

        assert "questions" in clarified
        assert "understanding_level" in clarified

        # Generate outline based on clarification
        outline = await orchestrator._generate_outline(clarified)

        assert "title" in outline
        assert "sections" in outline
        assert len(outline["sections"]) > 0

    @pytest.mark.asyncio
    async def test_parallel_slide_generation(self, orchestrator):
        """Test parallel slide generation."""

        outline = {
            "title": "Test Presentation",
            "sections": [
                {"title": "Section 1", "points": ["Point 1"]},
                {"title": "Section 2", "points": ["Point 2"]},
                {"title": "Section 3", "points": ["Point 3"]}
            ]
        }

        research = {}

        # Generate slides in parallel
        start_time = asyncio.get_event_loop().time()
        slides = await orchestrator._generate_slides_parallel(
            outline, research
        )
        duration = asyncio.get_event_loop().time() - start_time

        assert len(slides) == 3

        # Verify parallel execution (should be faster than sequential)
        assert duration < 10  # Assuming each slide takes ~5s sequentially
```

### Testing A2A Communication

```python
# tests/test_a2a_communication.py
import pytest
import httpx
from unittest.mock import AsyncMock

class TestA2ACommunication:
    """Test A2A protocol communication."""

    @pytest.mark.asyncio
    async def test_a2a_message_format(self):
        """Test A2A message format compliance."""
        from a2a_client import A2AClient

        client = A2AClient("http://localhost:10001")

        # Mock HTTP client
        client.client = AsyncMock()
        client.client.post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {
                "status": "success",
                "result": {"questions": []}
            }
        )

        message = {"user_request": "Test"}
        response = await client.send_message(message, stream=False)

        # Verify message was sent correctly
        client.client.post.assert_called_once()
        call_args = client.client.post.call_args
        assert call_args[1]["json"] == message

    @pytest.mark.asyncio
    async def test_a2a_streaming(self):
        """Test A2A streaming response."""
        from a2a_client import A2AClient

        client = A2AClient("http://localhost:10001")

        # Mock streaming response
        async def mock_stream():
            yield "data: {\"chunk\": \"test1\"}\n"
            yield "data: {\"chunk\": \"test2\"}\n"
            yield "data: [DONE]\n"

        client.client.stream = AsyncMock(return_value=mock_stream())

        chunks = []
        async for chunk in client.send_message({"test": "data"}):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0]["chunk"] == "test1"
        assert chunks[1]["chunk"] == "test2"
```

## Performance Testing

### Load Testing Single Agent

```python
# tests/test_performance.py
import asyncio
import time
import statistics
from typing import List

class AgentPerformanceTester:
    """Performance testing for agents."""

    def __init__(self, agent_url: str):
        self.agent_url = agent_url
        self.results = []

    async def run_single_test(self, test_id: int):
        """Run a single performance test."""
        start = time.time()

        try:
            # Send request to agent
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.agent_url}/message",
                    json={"test_id": test_id, "user_request": f"Test {test_id}"},
                    timeout=30
                )
                response.raise_for_status()

            duration = time.time() - start
            return {
                "test_id": test_id,
                "success": True,
                "duration": duration,
                "tokens": response.json().get("tokens_used", 0)
            }

        except Exception as e:
            duration = time.time() - start
            return {
                "test_id": test_id,
                "success": False,
                "duration": duration,
                "error": str(e)
            }

    async def run_load_test(
        self,
        num_requests: int = 100,
        concurrent: int = 10
    ):
        """Run load test with specified concurrency."""

        print(f"Starting load test: {num_requests} requests, {concurrent} concurrent")

        all_results = []

        for batch_start in range(0, num_requests, concurrent):
            batch_end = min(batch_start + concurrent, num_requests)
            batch_tasks = [
                self.run_single_test(i)
                for i in range(batch_start, batch_end)
            ]

            batch_results = await asyncio.gather(*batch_tasks)
            all_results.extend(batch_results)

            # Brief pause between batches
            await asyncio.sleep(0.1)

        self.analyze_results(all_results)
        return all_results

    def analyze_results(self, results: List[Dict]):
        """Analyze performance test results."""

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        if successful:
            durations = [r["duration"] for r in successful]

            print("\n=== Performance Test Results ===")
            print(f"Total Requests: {len(results)}")
            print(f"Successful: {len(successful)}")
            print(f"Failed: {len(failed)}")
            print(f"\nLatency Statistics:")
            print(f"  Mean: {statistics.mean(durations):.2f}s")
            print(f"  Median: {statistics.median(durations):.2f}s")
            print(f"  Min: {min(durations):.2f}s")
            print(f"  Max: {max(durations):.2f}s")
            print(f"  Std Dev: {statistics.stdev(durations):.2f}s")

            # Percentiles
            sorted_durations = sorted(durations)
            p50 = sorted_durations[len(sorted_durations) // 2]
            p95 = sorted_durations[int(len(sorted_durations) * 0.95)]
            p99 = sorted_durations[int(len(sorted_durations) * 0.99)]

            print(f"\nPercentiles:")
            print(f"  P50: {p50:.2f}s")
            print(f"  P95: {p95:.2f}s")
            print(f"  P99: {p99:.2f}s")

            # Token usage
            if any("tokens" in r for r in successful):
                tokens = [r.get("tokens", 0) for r in successful]
                print(f"\nToken Usage:")
                print(f"  Total: {sum(tokens)}")
                print(f"  Average: {statistics.mean(tokens):.0f}")

# Usage
async def main():
    tester = AgentPerformanceTester("http://localhost:10001")
    await tester.run_load_test(num_requests=50, concurrent=5)

if __name__ == "__main__":
    asyncio.run(main())
```

### Memory and Resource Testing

```python
# tests/test_resources.py
import psutil
import asyncio
import tracemalloc

class ResourceMonitor:
    """Monitor resource usage during agent execution."""

    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = None
        self.peak_memory = 0
        self.cpu_samples = []

    def start_monitoring(self):
        """Start resource monitoring."""
        tracemalloc.start()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory

    async def monitor_loop(self, duration: int = 60):
        """Monitor resources for specified duration."""

        for _ in range(duration):
            # Memory
            current_memory = self.process.memory_info().rss / 1024 / 1024
            self.peak_memory = max(self.peak_memory, current_memory)

            # CPU
            cpu_percent = self.process.cpu_percent(interval=0.1)
            self.cpu_samples.append(cpu_percent)

            await asyncio.sleep(1)

    def get_report(self):
        """Generate resource usage report."""

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            "memory": {
                "initial_mb": self.initial_memory,
                "peak_mb": self.peak_memory,
                "traced_current_mb": current / 1024 / 1024,
                "traced_peak_mb": peak / 1024 / 1024
            },
            "cpu": {
                "average_percent": sum(self.cpu_samples) / len(self.cpu_samples),
                "peak_percent": max(self.cpu_samples)
            }
        }

# Usage
async def test_agent_resources():
    monitor = ResourceMonitor()
    monitor.start_monitoring()

    # Start monitoring in background
    monitor_task = asyncio.create_task(monitor.monitor_loop(30))

    # Run agent tests
    # ... your agent execution code ...

    # Stop monitoring
    monitor_task.cancel()

    report = monitor.get_report()
    print(json.dumps(report, indent=2))
```

## Testing Multi-Agent Workflows

### Workflow Test Framework

```python
# tests/test_workflows.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import asyncio

@dataclass
class WorkflowStep:
    """Represents a step in a workflow test."""
    agent_name: str
    input_data: Dict[str, Any]
    expected_output_keys: List[str]
    timeout: int = 30
    should_fail: bool = False

class WorkflowTester:
    """Test multi-agent workflows."""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.results = []

    async def run_workflow_test(
        self,
        workflow_name: str,
        steps: List[WorkflowStep]
    ) -> Dict[str, Any]:
        """Run a complete workflow test."""

        print(f"Testing workflow: {workflow_name}")

        workflow_result = {
            "name": workflow_name,
            "steps": [],
            "success": True,
            "total_duration": 0
        }

        state = {}

        for i, step in enumerate(steps):
            print(f"  Step {i+1}: {step.agent_name}")

            start = asyncio.get_event_loop().time()

            try:
                # Execute agent
                result = await self.execute_step(step, state)

                duration = asyncio.get_event_loop().time() - start

                # Verify output
                if not step.should_fail:
                    for key in step.expected_output_keys:
                        assert key in result, f"Missing key: {key}"

                # Update state
                state.update(result)

                workflow_result["steps"].append({
                    "agent": step.agent_name,
                    "success": True,
                    "duration": duration
                })

            except Exception as e:
                duration = asyncio.get_event_loop().time() - start

                if not step.should_fail:
                    workflow_result["success"] = False
                    print(f"    ERROR: {str(e)}")

                workflow_result["steps"].append({
                    "agent": step.agent_name,
                    "success": False,
                    "duration": duration,
                    "error": str(e)
                })

                if not step.should_fail:
                    break

            workflow_result["total_duration"] += duration

        return workflow_result

    async def execute_step(
        self,
        step: WorkflowStep,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""

        # Merge input with current state
        input_data = {**state, **step.input_data}

        # Call appropriate agent method
        if step.agent_name == "clarifier":
            return await self.orchestrator._clarify_request(
                input_data["user_request"]
            )
        elif step.agent_name == "outline":
            return await self.orchestrator._generate_outline(
                input_data
            )
        # ... other agents ...

        raise ValueError(f"Unknown agent: {step.agent_name}")

# Example test
async def test_presentation_workflow():
    """Test complete presentation generation workflow."""

    orchestrator = PresentationOrchestrator()
    tester = WorkflowTester(orchestrator)

    workflow = [
        WorkflowStep(
            agent_name="clarifier",
            input_data={"user_request": "AI presentation"},
            expected_output_keys=["questions", "understanding_level"]
        ),
        WorkflowStep(
            agent_name="outline",
            input_data={},
            expected_output_keys=["title", "sections"]
        ),
        WorkflowStep(
            agent_name="slide_writer",
            input_data={},
            expected_output_keys=["slides"]
        )
    ]

    result = await tester.run_workflow_test(
        "basic_presentation",
        workflow
    )

    print(json.dumps(result, indent=2))
```

## PresentationPro Testing Strategy

### Test Pyramid

```
         /\
        /  \  E2E Tests (10%)
       /    \   - Full presentation generation
      /______\    - User journey tests
     /        \
    /          \  Integration Tests (30%)
   /            \   - Agent chains
  /______________\    - A2A communication
 /                \     - Database integration
/                  \
/__________________\  Unit Tests (60%)
                        - Individual agents
                        - Tools and utilities
                        - Input validation
```

### Testing Matrix

| Agent | Unit Tests | Integration | Performance | E2E |
|-------|------------|-------------|-------------|-----|
| Clarifier | ✓ Input validation<br>✓ Question generation<br>✓ Understanding scoring | ✓ With Outline | ✓ Load test<br>✓ Latency | ✓ |
| Outline | ✓ Structure generation<br>✓ Section creation | ✓ With SlideWriter | ✓ Load test | ✓ |
| SlideWriter | ✓ Content generation<br>✓ Note creation | ✓ With Critic | ✓ Parallel gen | ✓ |
| Critic | ✓ Review logic<br>✓ Scoring | ✓ With Polish | ✓ Load test | ✓ |
| NotesPolisher | ✓ Enhancement logic | ✓ With Script | ✓ Load test | ✓ |
| Design | ✓ Theme generation<br>✓ Visual suggestions | ✓ Standalone | ✓ Load test | ✓ |
| ScriptWriter | ✓ Script assembly | ✓ Final output | ✓ Load test | ✓ |
| Research | ✓ Search integration<br>✓ Data extraction | ✓ With Outline | ✓ API limits | ✓ |

### Continuous Testing Pipeline

```yaml
# .github/workflows/test.yml
name: ADK Agent Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run unit tests
        run: |
          pytest tests/unit --cov=agents --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2

  integration-tests:
    runs-on: ubuntu-latest
    services:
      arangodb:
        image: arangodb:latest
        ports:
          - 8530:8530

    steps:
      - uses: actions/checkout@v2

      - name: Start A2A servers
        run: |
          docker-compose up -d
          sleep 10

      - name: Run integration tests
        run: |
          pytest tests/integration --timeout=60

  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v2

      - name: Run performance tests
        run: |
          python tests/performance/run_load_tests.py

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: performance-results
          path: performance-results.json
```

## Automated Testing Pipeline

### Test Orchestration Script

```python
# run_all_tests.py
#!/usr/bin/env python3
"""
Comprehensive test runner for PresentationPro ADK agents.
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

class TestRunner:
    """Orchestrates all test types."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "unit": {},
            "integration": {},
            "performance": {},
            "e2e": {}
        }

    async def run_all_tests(self):
        """Run complete test suite."""

        print("=" * 50)
        print("PresentationPro ADK Test Suite")
        print("=" * 50)

        # 1. Unit Tests
        print("\n1. Running Unit Tests...")
        await self.run_unit_tests()

        # 2. Integration Tests
        print("\n2. Running Integration Tests...")
        await self.run_integration_tests()

        # 3. Performance Tests
        print("\n3. Running Performance Tests...")
        await self.run_performance_tests()

        # 4. E2E Tests
        print("\n4. Running E2E Tests...")
        await self.run_e2e_tests()

        # Generate report
        self.generate_report()

    async def run_unit_tests(self):
        """Execute unit tests."""
        import subprocess

        result = subprocess.run(
            ["pytest", "tests/unit", "-v", "--json-report"],
            capture_output=True,
            text=True
        )

        self.results["unit"] = {
            "passed": result.returncode == 0,
            "output": result.stdout
        }

    async def run_integration_tests(self):
        """Execute integration tests."""
        # Start services
        print("  Starting services...")

        # Run tests
        from tests.test_agent_integration import TestAgentIntegration

        test = TestAgentIntegration()
        orchestrator = await test.orchestrator()

        try:
            await test.test_clarifier_to_outline_flow(orchestrator)
            self.results["integration"]["clarifier_outline"] = "PASS"
        except Exception as e:
            self.results["integration"]["clarifier_outline"] = f"FAIL: {e}"

        await orchestrator.cleanup()

    async def run_performance_tests(self):
        """Execute performance tests."""
        from tests.test_performance import AgentPerformanceTester

        tester = AgentPerformanceTester("http://localhost:10001")
        results = await tester.run_load_test(
            num_requests=10,
            concurrent=2
        )

        self.results["performance"] = {
            "total_requests": len(results),
            "successful": len([r for r in results if r["success"]]),
            "average_latency": sum(r["duration"] for r in results) / len(results)
        }

    async def run_e2e_tests(self):
        """Execute end-to-end tests."""
        # Simulate complete user journey
        print("  Testing complete presentation generation...")

        # Implementation depends on your E2E framework
        self.results["e2e"]["full_generation"] = "PASS"

    def generate_report(self):
        """Generate test report."""

        # Save JSON report
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # Print summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)

        print(f"\nUnit Tests: {'PASS' if self.results['unit'].get('passed') else 'FAIL'}")

        integration_passed = all(
            "PASS" in str(v)
            for v in self.results["integration"].values()
        )
        print(f"Integration Tests: {'PASS' if integration_passed else 'FAIL'}")

        perf = self.results["performance"]
        if perf:
            print(f"Performance Tests: {perf['successful']}/{perf['total_requests']} passed")
            print(f"  Average Latency: {perf['average_latency']:.2f}s")

        e2e_passed = all(
            v == "PASS"
            for v in self.results["e2e"].values()
        )
        print(f"E2E Tests: {'PASS' if e2e_passed else 'FAIL'}")

if __name__ == "__main__":
    runner = TestRunner()
    asyncio.run(runner.run_all_tests())
```

## Best Practices

### 1. Test Data Management

```python
# tests/fixtures/test_data.py
"""Centralized test data management."""

TEST_PRESENTATIONS = {
    "simple": {
        "request": "Create a 5-slide presentation about cats",
        "expected_slides": 5,
        "audience": "general"
    },
    "complex": {
        "request": "Technical presentation on quantum computing for PhD students",
        "expected_slides": 15,
        "audience": "academic"
    }
}

def get_test_case(name: str):
    """Get test case by name."""
    return TEST_PRESENTATIONS.get(name)
```

### 2. Mock Services

```python
# tests/mocks/llm_mock.py
"""Mock LLM for testing."""

class MockLLM:
    """Mock LLM that returns predictable responses."""

    def __init__(self, responses: Dict[str, Any]):
        self.responses = responses
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        """Generate mock response."""
        self.call_count += 1

        # Return response based on prompt content
        if "clarify" in prompt.lower():
            return json.dumps(self.responses.get("clarifier", {}))
        elif "outline" in prompt.lower():
            return json.dumps(self.responses.get("outline", {}))

        return "{}"
```

### 3. Test Isolation

```python
# tests/conftest.py
"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_workspace():
    """Create isolated workspace for tests."""
    workspace = tempfile.mkdtemp()
    yield Path(workspace)
    shutil.rmtree(workspace)

@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock API key for tests."""
    monkeypatch.setenv("GOOGLE_GENAI_API_KEY", "test-key-123")
```

### 4. Test Documentation

```python
# tests/README.md
"""
# PresentationPro Test Suite

## Running Tests

### All Tests
```bash
python run_all_tests.py
```

### Specific Categories
```bash
pytest tests/unit           # Unit tests only
pytest tests/integration    # Integration tests
pytest tests/performance    # Performance tests
pytest tests/e2e           # End-to-end tests
```

### With Coverage
```bash
pytest --cov=agents --cov-report=html
```

## Test Structure
- `unit/` - Isolated agent tests
- `integration/` - Multi-agent tests
- `performance/` - Load and latency tests
- `e2e/` - Full workflow tests
- `fixtures/` - Test data
- `mocks/` - Mock services
"""
```

## Next Steps

1. Implement comprehensive unit tests for all agents
2. Set up continuous integration pipeline
3. Add performance benchmarks
4. Create E2E test scenarios
5. Implement test coverage reporting
6. Add mutation testing for quality assurance