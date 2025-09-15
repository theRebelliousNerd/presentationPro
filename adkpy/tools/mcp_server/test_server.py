"""
Test script for MCP Server

Run this to verify the server is working correctly.
"""

import asyncio
import json
import sys
from typing import Any, Dict

import httpx


class MCPServerTester:
    """Test client for MCP Server"""

    def __init__(self, base_url: str = "http://localhost:8090"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_health(self) -> Dict[str, Any]:
        """Test health endpoint"""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json()

    async def test_list_tools(self) -> Dict[str, Any]:
        """Test listing tools"""
        response = await self.client.post(
            f"{self.base_url}/tools/list",
            json={"includeDeprecated": False}
        )
        return response.json()

    async def test_web_search(self) -> Dict[str, Any]:
        """Test web search tool"""
        response = await self.client.post(
            f"{self.base_url}/tools/call",
            json={
                "name": "web_search",
                "arguments": {
                    "query": "Model Context Protocol",
                    "top_k": 3
                }
            }
        )
        return response.json()

    async def test_telemetry_record(self) -> Dict[str, Any]:
        """Test telemetry recording"""
        response = await self.client.post(
            f"{self.base_url}/tools/call",
            json={
                "name": "telemetry_record",
                "arguments": {
                    "step": "test_step",
                    "agent": "test_agent",
                    "promptTokens": 100,
                    "completionTokens": 50
                }
            }
        )
        return response.json()

    async def test_telemetry_aggregate(self) -> Dict[str, Any]:
        """Test telemetry aggregation"""
        response = await self.client.post(
            f"{self.base_url}/tools/call",
            json={
                "name": "telemetry_aggregate",
                "arguments": {}
            }
        )
        return response.json()

    async def test_mcp_protocol(self) -> Dict[str, Any]:
        """Test MCP protocol endpoint"""
        response = await self.client.post(
            f"{self.base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
        )
        # This returns SSE stream, so we just check status
        return {"status_code": response.status_code}

    async def run_all_tests(self):
        """Run all tests"""
        print("=" * 50)
        print("MCP Server Test Suite")
        print("=" * 50)

        tests = [
            ("Health Check", self.test_health),
            ("List Tools", self.test_list_tools),
            ("Web Search", self.test_web_search),
            ("Telemetry Record", self.test_telemetry_record),
            ("Telemetry Aggregate", self.test_telemetry_aggregate),
            ("MCP Protocol", self.test_mcp_protocol),
        ]

        results = {}
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            print("-" * 30)
            try:
                result = await test_func()
                results[test_name] = {"status": "PASS", "data": result}
                print(f"✅ {test_name} passed")
                if isinstance(result, dict):
                    print(f"Response: {json.dumps(result, indent=2)[:200]}...")
            except Exception as e:
                results[test_name] = {"status": "FAIL", "error": str(e)}
                print(f"❌ {test_name} failed: {e}")

        # Summary
        print("\n" + "=" * 50)
        print("Test Summary")
        print("=" * 50)
        passed = sum(1 for r in results.values() if r["status"] == "PASS")
        failed = sum(1 for r in results.values() if r["status"] == "FAIL")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Total: {len(results)}")

        await self.client.aclose()
        return results


async def main():
    """Main test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="Test MCP Server")
    parser.add_argument(
        "--url",
        default="http://localhost:8090",
        help="MCP Server URL"
    )
    args = parser.parse_args()

    tester = MCPServerTester(args.url)
    results = await tester.run_all_tests()

    # Exit with error if any tests failed
    if any(r["status"] == "FAIL" for r in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())