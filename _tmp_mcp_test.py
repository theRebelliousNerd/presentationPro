import asyncio, base64, io
from fastmcp import Client
from PIL import Image, ImageDraw

async def main():
    async with Client('http://127.0.0.1:9170/mcp') as c:
        img=Image.new('RGB',(200,150),'white')
        d=ImageDraw.Draw(img)
        d.rectangle([10,10,190,30], fill='#000')
        buf=io.BytesIO(); img.save(buf, format='PNG')
        data='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
        res=await c.call_tool('critic.assess_blur', {'imageDataUrl': data})
        print(res.data)

asyncio.run(main())
