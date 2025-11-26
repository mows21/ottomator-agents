"""
Google ADK Platform
===================

Google Agent Development Kit (Gemini 3 Pro) integration.

Features:
- Gemini 2.0 Flash and Pro model support
- Google Search grounding
- Function calling
- Code execution
- Multi-modal capabilities

This platform provides agents built with Google's ADK.
"""

from platforms.google_adk.agent import GoogleADKAgent, GoogleADKConfig
from platforms.google_adk.tools import GoogleTool, create_google_search_tool

__all__ = [
    "GoogleADKAgent",
    "GoogleADKConfig",
    "GoogleTool",
    "create_google_search_tool",
]
