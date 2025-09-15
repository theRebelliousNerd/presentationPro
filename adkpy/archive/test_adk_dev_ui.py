#!/usr/bin/env python
"""
Test script for ADK Dev UI

This script tests the ADK Dev UI integration and demonstrates:
1. Agent registration with decorators
2. Dev UI endpoints
3. WebSocket communication
4. Agent discovery
"""

import asyncio
import json
import logging
import requests
import websockets
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8089"
WS_URL = "ws://localhost:8089"


def test_health_check():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        assert data["ok"] == True
        assert data["dev_ui"] == True
        logger.info("✓ Health check passed")
        return True
    except Exception as e:
        logger.error(f"✗ Health check failed: {e}")
        return False


def test_dev_ui_home():
    """Test the Dev UI home page."""
    try:
        response = requests.get(f"{BASE_URL}/adk-dev")
        assert response.status_code == 200
        assert "ADK Development UI" in response.text
        logger.info("✓ Dev UI home page accessible")
        return True
    except Exception as e:
        logger.error(f"✗ Dev UI home page failed: {e}")
        return False


def test_agent_discovery():
    """Test agent discovery endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/adk-dev/api/agents")
        agents = response.json()
        logger.info(f"✓ Discovered {len(agents)} agents:")

        for agent in agents:
            logger.info(f"  - {agent['name']} v{agent['version']}: {agent['description'][:50]}...")

        return len(agents) > 0
    except Exception as e:
        logger.error(f"✗ Agent discovery failed: {e}")
        return False


def test_agent_details(agent_name: str = "clarifier"):
    """Test getting detailed agent information."""
    try:
        response = requests.get(f"{BASE_URL}/adk-dev/api/agent/{agent_name}")

        if response.status_code == 404:
            logger.warning(f"Agent '{agent_name}' not found")
            return False

        agent = response.json()
        logger.info(f"✓ Agent details for '{agent_name}':")
        logger.info(f"  - Version: {agent.get('version')}")
        logger.info(f"  - Category: {agent.get('category')}")
        logger.info(f"  - Tools: {agent.get('tools', [])}")

        return True
    except Exception as e:
        logger.error(f"✗ Agent details failed: {e}")
        return False


async def test_websocket_chat(agent_name: str = "clarifier"):
    """Test WebSocket chat with an agent."""
    try:
        session_id = "test-session-123"
        uri = f"{WS_URL}/adk-dev/ws/agent/{agent_name}?session_id={session_id}"

        async with websockets.connect(uri) as websocket:
            logger.info(f"✓ Connected to WebSocket for agent '{agent_name}'")

            # Send a test message
            test_message = {
                "type": "request",
                "agent_id": agent_name,
                "message": "I need to create a presentation about artificial intelligence",
                "trace_enabled": True
            }

            await websocket.send(json.dumps(test_message))
            logger.info("✓ Sent test message")

            # Receive responses
            responses_received = 0
            max_responses = 3  # Limit to avoid infinite loop

            while responses_received < max_responses:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)

                    if data["type"] == "response":
                        logger.info(f"✓ Received response: {data.get('content', '')[:100]}...")
                        responses_received += 1
                    elif data["type"] == "event":
                        logger.info(f"  Event: {data.get('content')}")
                    elif data["type"] == "error":
                        logger.error(f"  Error: {data.get('content')}")
                        break

                except asyncio.TimeoutError:
                    logger.info("  No more responses (timeout)")
                    break

            return responses_received > 0

    except Exception as e:
        logger.error(f"✗ WebSocket chat failed: {e}")
        return False


def test_http_chat(agent_name: str = "clarifier"):
    """Test HTTP chat endpoint with an agent."""
    try:
        chat_request = {
            "agent_id": agent_name,
            "message": "What should I include in a presentation about climate change?",
            "context": {},
            "trace_enabled": True
        }

        response = requests.post(
            f"{BASE_URL}/adk-dev/api/agent/{agent_name}/chat",
            json=chat_request
        )

        if response.status_code == 404:
            logger.warning(f"Agent '{agent_name}' not found for chat")
            return False

        if response.status_code != 200:
            logger.error(f"Chat request failed with status {response.status_code}")
            return False

        data = response.json()
        logger.info(f"✓ HTTP chat successful:")
        logger.info(f"  Response: {str(data.get('response'))[:100]}...")

        if data.get('usage'):
            logger.info(f"  Tokens used: {data['usage'].get('totalTokens', 0)}")

        return True

    except Exception as e:
        logger.error(f"✗ HTTP chat failed: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("ADK Dev UI Test Suite")
    logger.info("=" * 60)

    results = []

    # Basic connectivity tests
    logger.info("\n1. Testing Basic Connectivity...")
    results.append(("Health Check", test_health_check()))
    results.append(("Dev UI Home", test_dev_ui_home()))

    # Agent discovery tests
    logger.info("\n2. Testing Agent Discovery...")
    results.append(("Agent Discovery", test_agent_discovery()))
    results.append(("Agent Details", test_agent_details()))

    # Chat tests
    logger.info("\n3. Testing Chat Functionality...")
    results.append(("HTTP Chat", test_http_chat()))

    # WebSocket test (async)
    logger.info("\n4. Testing WebSocket Communication...")
    ws_result = await test_websocket_chat()
    results.append(("WebSocket Chat", ws_result))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary:")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {test_name:20} {status}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 All tests passed! ADK Dev UI is working correctly.")
    else:
        logger.warning(f"\n⚠️  {total - passed} test(s) failed. Please check the logs above.")

    return passed == total


def main():
    """Main entry point."""
    logger.info("Starting ADK Dev UI tests...")
    logger.info(f"Testing against: {BASE_URL}")
    logger.info("Make sure the ADK backend is running with: docker compose up adkpy")
    logger.info("")

    # Run the async test suite
    success = asyncio.run(run_all_tests())

    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()