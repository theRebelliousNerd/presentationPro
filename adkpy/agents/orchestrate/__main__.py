"""
Main entry point for the orchestrate agent when run as a module.
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

# Import the agent module
from . import agent

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# The agent module handles initialization
log.info("Starting orchestrator agent...")

# Keep the container running
log.info("Orchestrator agent is ready. Keeping container alive...")
try:
    # Simple sleep loop to keep container alive
    while True:
        asyncio.run(asyncio.sleep(60))
except KeyboardInterrupt:
    log.info("Orchestrator shutting down...")
    exit(0)