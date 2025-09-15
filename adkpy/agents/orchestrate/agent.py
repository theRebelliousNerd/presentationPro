"""
Main entry point for the orchestrate agent.
Uses the simplified orchestrate_agent module.
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

# Import the simple orchestrator
from simple_orchestrate_agent import root_agent

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Get remote agent addresses from environment
REMOTE_AGENT_ADDRESSES_STR = os.getenv("REMOTE_AGENT_ADDRESSES", "")
log.info(f"Remote Agent Addresses String: {REMOTE_AGENT_ADDRESSES_STR}")
REMOTE_AGENT_ADDRESSES = [addr.strip() for addr in REMOTE_AGENT_ADDRESSES_STR.split(',') if addr.strip()]
log.info(f"Remote Agent Addresses: {REMOTE_AGENT_ADDRESSES}")

# The root_agent is already created by simple_orchestrate_agent.py
log.info(f"Orchestrator root agent '{root_agent.name}' created.")
log.info("Note: Using simple orchestrator without remote A2A connections for now")

# Keep the container running
if __name__ == "__main__":
    log.info("Orchestrator agent is ready. Keeping container alive...")
    # Keep the process running
    try:
        # Simple sleep loop to keep container alive
        while True:
            asyncio.run(asyncio.sleep(60))
    except KeyboardInterrupt:
        log.info("Orchestrator shutting down...")
        exit(0)