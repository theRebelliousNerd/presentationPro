"""Main entry point for the orchestration service."""

import asyncio
import logging
from dotenv import load_dotenv

if __package__:
    from .orchestrate_agent import orchestrator, run_workflow  # package context
else:  # pragma: no cover - executed when run as top-level module
    from orchestrate_agent import orchestrator, run_workflow

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

log.info("Presentation orchestrator initialised with API base %s", orchestrator.api_base)

if __name__ == "__main__":
    log.info("Orchestrator agent is ready. Keeping container alive...")
    try:
        while True:
            asyncio.run(asyncio.sleep(60))
    except KeyboardInterrupt:
        log.info("Orchestrator shutting down...")
        raise SystemExit(0)
