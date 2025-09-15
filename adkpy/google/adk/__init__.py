"""
Google ADK compatibility module.

This module redirects imports from google.adk to the local adk implementation.
"""

# Import everything from the local adk module
import sys
import os

# Add parent directory to path to import local adk
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import from local adk
from adk import *

# Also make submodules available
from adk import agents, tools, types, dev_ui