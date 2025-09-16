import asyncio
from fastmcp import Client
async def main():
    async with Client('http://127.0.0.1:9170/mcp') as c:
        lt = await c.list_tools()
        print([t.name for t in lt.tools])
asyncio.run(main())
