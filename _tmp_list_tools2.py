import asyncio
from fastmcp import Client
async def main():
    async with Client('http://127.0.0.1:9170/mcp') as c:
        lt = await c.list_tools()
        names = [getattr(t,'name',None) or t.get('name') for t in (lt.tools if hasattr(lt,'tools') else lt)]
        print(names)
asyncio.run(main())
