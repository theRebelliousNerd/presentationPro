#!/usr/bin/env python3
"""
Launch ADK Dev UI for PresentationPro agents.

Prefers the Google ADK CLI web server (`adk web`) when it is available so we
use the official agent UX. Falls back to the minimal local FastAPI view when
running offline or if the CLI is missing.
"""

from __future__ import annotations

import os
import shlex
import shutil
import sys
from pathlib import Path

# --------------------------------------------------------------------------------------
# Helpers


def _exec_adk_web(agents_dir: Path) -> None:
    """Replace the current process with `adk web` if the CLI exists."""
    adk_bin = shutil.which("adk")
    if not adk_bin:
        raise FileNotFoundError("'adk' CLI not found on PATH")

    host = os.environ.get("ADK_DEV_HOST", "0.0.0.0")
    port = os.environ.get("ADK_DEV_PORT", "8100")
    extra = os.environ.get("ADK_DEV_WEB_ARGS", "")

    cmd = [adk_bin, "web", "--host", host, "--port", str(port)]
    if extra.strip():
        cmd.extend(shlex.split(extra))
    cmd.append(str(agents_dir))

    print("=" * 60, flush=True)
    print("Launching Google ADK Web UI", flush=True)
    print("=" * 60, flush=True)
    print(f"Binary: {adk_bin}", flush=True)
    print(f"Agents dir: {agents_dir}", flush=True)
    print(f"Host: {host}  Port: {port}", flush=True)
    if extra.strip():
        print(f"Extra args: {extra}", flush=True)
    print("Delegating to: " + " ".join(cmd), flush=True)

    env = os.environ.copy()
    py_path_parts = [str(agents_dir), str(agents_dir.parent)]
    if env.get("PYTHONPATH"):
        py_path_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(filter(None, py_path_parts))

    os.execve(adk_bin, cmd, env)


def _fallback_local_ui(script_dir: Path) -> None:
    """Start the lightweight bundled FastAPI UI as a fallback."""
    try:
        from adk.dev_ui import get_dev_ui_server
        import uvicorn
    except ImportError:
        print("Error: Google ADK not installed and local fallback unavailable")
        print("Please install it with: pip install google-adk")
        sys.exit(1)

    agents_list = []
    agent_names = []

    def _try_import(module: str, label: str) -> None:
        try:
            mod = __import__(module, fromlist=("root_agent",))
            root = getattr(mod, "root_agent", None)
            if root:
                agents_list.append(root)
                agent_names.append(label)
        except ImportError as err:  # noqa: PERF203 - clarity over micro perf
            print(f"Warning: Could not import {label} agent: {err}")

    # Import each agent's root_agent explicitly
    _try_import("agents.clarifier.agent", "clarifier")
    _try_import("agents.outline.agent", "outline")
    _try_import("agents.slide_writer.agent", "slide_writer")
    _try_import("agents.critic.agent", "critic")
    _try_import("agents.notes_polisher.agent", "notes_polisher")
    _try_import("agents.design.agent", "design")
    _try_import("agents.script_writer.agent", "script_writer")
    _try_import("agents.research.agent", "research")

    print("=" * 60)
    print("Launching fallback ADK Dev UI for PresentationPro Agents")
    print("=" * 60)
    print(f"Working directory: {script_dir}")
    api_key = os.environ.get("GOOGLE_GENAI_API_KEY", "")
    print(f"API Key: {'*' * 20}{api_key[-4:] if api_key else 'NONE'}")
    print()
    print(f"Successfully loaded {len(agents_list)} agents:")
    for name in agent_names:
        print(f"  - {name}")
    print()
    print("Agent Microservice Ports (when running standalone):")
    print("  - clarifier: 10001")
    print("  - outline: 10002")
    print("  - slide_writer: 10003")
    print("  - critic: 10004")
    print("  - notes_polisher: 10005")
    print("  - design: 10006")
    print("  - script_writer: 10007")
    print("  - research: 10008")
    print()
    print("Starting fallback Dev UI on http://localhost:8100")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app = get_dev_ui_server(agents=agents_list, host="0.0.0.0", port=8100, title="PresentationPro Agents")
    uvicorn.run(app, host="0.0.0.0", port=8100, log_level="info")


def _resolve_agents_dir(script_dir: Path) -> Path | None:
    """Determine which agents directory to use."""
    env_path = os.environ.get("ADK_DEV_AGENT_DIR")
    if env_path:
        return Path(env_path)

    candidates = [script_dir / "agents", script_dir / "adkpy" / "agents"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


# --------------------------------------------------------------------------------------
# Entry point


def main() -> None:
    script_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(script_dir))

    api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
    if not api_key:
        print("Error: GOOGLE_GENAI_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_GENAI_API_KEY=your_key_here")
        sys.exit(1)

    agents_dir = _resolve_agents_dir(script_dir)

    if agents_dir and agents_dir.exists():
        try:
            _exec_adk_web(agents_dir)
        except Exception as exc:  # noqa: BLE001 - we need to surface errors to fallback
            print(f"Warning: failed to launch ADK Web UI via 'adk web': {exc}")
            print("Falling back to bundled lightweight UI...")
    else:
        missing = os.environ.get("ADK_DEV_AGENT_DIR") or "/app/agents"
        print(f"Warning: agents directory {missing} not found; falling back to bundled UI...")

    _fallback_local_ui(script_dir)


if __name__ == "__main__":
    main()

