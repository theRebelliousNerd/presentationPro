import os
import subprocess
import sys
import time

def main():
    # Start services
    subprocess.run(["docker", "compose", "up", "-d", "visioncv", "api-gateway"], check=True)
    # Allow warm-up
    time.sleep(3)
    # Run integration test
    env = os.environ.copy()
    env.setdefault("GATEWAY", "http://localhost:18088")
    cmd = [sys.executable, "adkpy/tests/integration/test_visioncv_proxy.py"]
    subprocess.run(cmd, env=env, check=True)

if __name__ == "__main__":
    main()

