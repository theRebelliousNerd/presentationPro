"""
Test Script for A2A-based Multi-Agent System

This script tests the complete presentation generation workflow
using the new A2A protocol-based architecture.
"""

import asyncio
import httpx
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
ORCHESTRATOR_URL = "http://localhost:8088"


class PresentationWorkflowTester:
    """Test harness for the presentation generation workflow."""

    def __init__(self):
        """Initialize the tester."""
        self.client = httpx.AsyncClient(base_url=ORCHESTRATOR_URL, timeout=60.0)
        self.session_id = None
        self.test_results = []

    async def test_health_check(self) -> bool:
        """Test the orchestrator health endpoint."""
        try:
            logger.info("Testing health check...")
            response = await self.client.get("/health")
            response.raise_for_status()
            data = response.json()

            logger.info(f"Health status: {data.get('status')}")
            logger.info(f"Connected agents: {data.get('agents')}")

            self.test_results.append({
                "test": "health_check",
                "passed": data.get("status") == "healthy",
                "details": data
            })

            return data.get("status") == "healthy"

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.test_results.append({
                "test": "health_check",
                "passed": False,
                "error": str(e)
            })
            return False

    async def test_clarification(self) -> bool:
        """Test the clarification workflow."""
        try:
            logger.info("Testing clarification workflow...")

            # Initial clarification request
            request = {
                "history": [],
                "initialInput": {
                    "text": "I need to create a presentation about AI",
                    "audience": "tech executives",
                    "tone": "professional"
                }
            }

            response = await self.client.post("/v1/clarify", json=request)
            response.raise_for_status()
            data = response.json()

            self.session_id = data.get("session_id")
            logger.info(f"Session ID: {self.session_id}")
            logger.info(f"Clarifier response: {data.get('refinedGoals')[:100]}...")
            logger.info(f"Finished: {data.get('finished')}")

            # Second round of clarification
            if not data.get("finished"):
                request["history"] = [
                    {"role": "assistant", "content": data.get("refinedGoals")},
                    {"role": "user", "content": "The presentation should be 10 slides, focusing on practical applications"}
                ]
                request["session_id"] = self.session_id

                response = await self.client.post("/v1/clarify", json=request)
                response.raise_for_status()
                data = response.json()

                logger.info(f"Second response: {data.get('refinedGoals')[:100]}...")

            self.test_results.append({
                "test": "clarification",
                "passed": True,
                "session_id": self.session_id
            })

            return True

        except Exception as e:
            logger.error(f"Clarification test failed: {e}")
            self.test_results.append({
                "test": "clarification",
                "passed": False,
                "error": str(e)
            })
            return False

    async def test_outline_generation(self) -> bool:
        """Test outline generation."""
        try:
            logger.info("Testing outline generation...")

            request = {
                "refinedGoals": "Create a 10-slide presentation about AI for tech executives, focusing on practical applications and ROI",
                "session_id": self.session_id
            }

            response = await self.client.post("/v1/outline", json=request)
            response.raise_for_status()
            data = response.json()

            outline = data.get("outline", {})
            logger.info(f"Generated outline with {len(outline.get('slides', []))} slides")

            self.test_results.append({
                "test": "outline_generation",
                "passed": bool(outline),
                "slide_count": len(outline.get('slides', []))
            })

            return bool(outline)

        except Exception as e:
            logger.error(f"Outline generation test failed: {e}")
            self.test_results.append({
                "test": "outline_generation",
                "passed": False,
                "error": str(e)
            })
            return False

    async def test_slide_generation(self) -> bool:
        """Test slide generation with all enhancements."""
        try:
            logger.info("Testing slide generation...")

            # Generate a test slide
            request = {
                "slideNumber": 1,
                "outline": {
                    "title": "AI in Business",
                    "slides": [
                        {
                            "number": 1,
                            "title": "Introduction to AI",
                            "points": ["What is AI?", "Why it matters", "Business impact"]
                        }
                    ]
                },
                "refinedGoals": "Focus on practical AI applications",
                "session_id": self.session_id
            }

            response = await self.client.post("/v1/slide/write", json=request)
            response.raise_for_status()
            data = response.json()

            slide = data.get("slide", {})
            logger.info(f"Generated slide: {slide.get('title')}")
            logger.info(f"Has speaker notes: {bool(slide.get('speakerNotes'))}")
            logger.info(f"Has design: {bool(slide.get('design'))}")

            self.test_results.append({
                "test": "slide_generation",
                "passed": bool(slide),
                "has_content": bool(slide.get("content")),
                "has_notes": bool(slide.get("speakerNotes")),
                "has_design": bool(slide.get("design"))
            })

            return bool(slide)

        except Exception as e:
            logger.error(f"Slide generation test failed: {e}")
            self.test_results.append({
                "test": "slide_generation",
                "passed": False,
                "error": str(e)
            })
            return False

    async def test_agent_discovery(self) -> bool:
        """Test agent discovery."""
        try:
            logger.info("Testing agent discovery...")

            response = await self.client.get("/v1/agents")
            response.raise_for_status()
            data = response.json()

            agents = data.get("agents", [])
            logger.info(f"Discovered {len(agents)} agents:")
            for agent in agents:
                logger.info(f"  - {agent['name']} v{agent['version']}")

            self.test_results.append({
                "test": "agent_discovery",
                "passed": len(agents) > 0,
                "agent_count": len(agents)
            })

            return len(agents) > 0

        except Exception as e:
            logger.error(f"Agent discovery test failed: {e}")
            self.test_results.append({
                "test": "agent_discovery",
                "passed": False,
                "error": str(e)
            })
            return False

    async def test_session_management(self) -> bool:
        """Test session management."""
        try:
            if not self.session_id:
                logger.warning("No session ID available, skipping session test")
                return False

            logger.info(f"Testing session management for {self.session_id}...")

            response = await self.client.get(f"/v1/sessions/{self.session_id}")
            response.raise_for_status()
            data = response.json()

            logger.info(f"Session state: {data.get('state')}")
            logger.info(f"Agent results: {list(data.get('agent_results', {}).keys())}")

            self.test_results.append({
                "test": "session_management",
                "passed": True,
                "session_state": data.get("state")
            })

            return True

        except Exception as e:
            logger.error(f"Session management test failed: {e}")
            self.test_results.append({
                "test": "session_management",
                "passed": False,
                "error": str(e)
            })
            return False

    async def run_all_tests(self):
        """Run all tests in sequence."""
        logger.info("Starting A2A system tests...")
        logger.info("=" * 50)

        # Run tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Agent Discovery", self.test_agent_discovery),
            ("Clarification", self.test_clarification),
            ("Outline Generation", self.test_outline_generation),
            ("Slide Generation", self.test_slide_generation),
            ("Session Management", self.test_session_management),
        ]

        for test_name, test_func in tests:
            logger.info(f"\nRunning test: {test_name}")
            logger.info("-" * 30)

            success = await test_func()

            if success:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")

            # Small delay between tests
            await asyncio.sleep(1)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50)

        passed = sum(1 for r in self.test_results if r.get("passed"))
        total = len(self.test_results)

        logger.info(f"Total tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Success rate: {(passed/total)*100:.1f}%")

        logger.info("\nDetailed Results:")
        for result in self.test_results:
            status = "✅ PASS" if result.get("passed") else "❌ FAIL"
            logger.info(f"  {result['test']}: {status}")
            if result.get("error"):
                logger.info(f"    Error: {result['error']}")

        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": total - passed
                },
                "results": self.test_results
            }, f, indent=2)

        logger.info("\nResults saved to test_results.json")

    async def cleanup(self):
        """Clean up resources."""
        await self.client.aclose()


async def main():
    """Main test runner."""
    tester = PresentationWorkflowTester()

    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   PresentationPro A2A System Integration Test   ║
    ╚══════════════════════════════════════════════════╝

    This test will validate the complete multi-agent
    presentation generation workflow using A2A protocol.

    Prerequisites:
    - Docker Compose stack running (docker-compose up)
    - All agents healthy and connected
    - MCP server operational

    Starting tests...
    """)

    asyncio.run(main())