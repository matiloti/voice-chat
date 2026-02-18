"""Agent tools — Brave Search integration."""

import os
import logging
from langchain_core.tools import tool

from config import settings

logger = logging.getLogger(__name__)


def get_brave_search_tool():
    """Create and return the Brave Search tool."""

    @tool
    def brave_search(query: str) -> str:
        """Search the web for current information using Brave Search.
        Use this when you need to find recent facts, news, documentation,
        or any information that may have changed or been published recently.
        """
        if not settings.brave_search_api_key:
            return "Brave Search API key not configured. Please set BRAVE_SEARCH_API_KEY in .env"

        try:
            from langchain_community.tools.brave_search.tool import BraveSearch as BraveSearchTool
            search = BraveSearchTool.from_api_key(
                api_key=settings.brave_search_api_key,
                search_kwargs={"count": 3},
            )
            return search.run(query)
        except Exception as e:
            logger.error("Brave search failed: %s", e)
            return f"Search failed: {str(e)}"

    return brave_search
