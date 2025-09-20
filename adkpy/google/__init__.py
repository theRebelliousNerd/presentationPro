"""
Google namespace package for ADK compatibility.

Extends the namespace so pip-installed "google" packages (including google-adk)
remain importable alongside our local stubs.
"""

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
