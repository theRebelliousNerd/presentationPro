import asyncio
import base64
import io
import os
import subprocess
import sys
import time
from PIL import Image, ImageDraw


def _mk_data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


async def run_client(port: int):
    from fastmcp import Client
    url = f"http://127.0.0.1:{port}/mcp"
    async with Client(url) as client:
        tools = await client.list_tools()
        # simple call: assess_blur
        img = Image.new("RGB", (200, 150), "white")
        d = ImageDraw.Draw(img)
        d.rectangle([10, 10, 190, 30], fill="#000")
        data_url = _mk_data_url(img)
        res = await client.call_tool("critic.assess_blur", {"imageDataUrl": data_url})
        print("HTTP MCP blur:", res.data)


def main():
    # start server
    port = 9172
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([env.get("PYTHONPATH", ""), os.path.abspath("visioncv")])
    proc = subprocess.Popen([sys.executable, "-m", "visioncv.agent", "--transport", "http", "--host", "127.0.0.1", "--port", str(port)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    try:
        # give server time to start
        time.sleep(3.0)
        asyncio.run(run_client(port))
    finally:
        try:
            # dump some logs
            out = proc.stdout.read(1000) if proc.stdout else ''
            if out:
                print('server logs:\n', out)
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
