"""Expose visioncv internal modules at the top level."""

import sys
from importlib import import_module

_core = import_module('.visioncv', __name__)
server = import_module('.visioncv.server', __name__)
tools = import_module('.visioncv.tools', __name__)

sys.modules[__name__ + '.server'] = server
sys.modules[__name__ + '.tools'] = tools

__all__ = ['server', 'tools']
