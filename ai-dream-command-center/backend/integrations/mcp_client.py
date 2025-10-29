"""MCP (Model Context Protocol) integration for AI Dream Command Center.

This module provides integration with MCP servers to extend agent capabilities
with external tools and data sources.
"""

from typing import Dict, List, Any, Optional
import httpx


class MCPClient:
    """Client for interacting with MCP servers."""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        try:
            response = await self.client.get(f"{self.server_url}/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error listing MCP tools: {e}")
            return []

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Call a tool on the MCP server."""
        try:
            response = await self.client.post(
                f"{self.server_url}/tools/{tool_name}",
                json={"arguments": arguments},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error calling MCP tool {tool_name}: {e}")
            return None

    async def get_resources(self) -> List[Dict[str, Any]]:
        """Get available resources from MCP server."""
        try:
            response = await self.client.get(f"{self.server_url}/resources")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting MCP resources: {e}")
            return []

    async def read_resource(self, resource_uri: str) -> Optional[str]:
        """Read a resource from MCP server."""
        try:
            response = await self.client.post(
                f"{self.server_url}/resources/read",
                json={"uri": resource_uri},
            )
            response.raise_for_status()
            return response.json().get("content")
        except Exception as e:
            print(f"Error reading MCP resource {resource_uri}: {e}")
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class MCPManager:
    """Manages multiple MCP server connections."""

    def __init__(self):
        self.servers: Dict[str, MCPClient] = {}

    def add_server(self, name: str, url: str):
        """Add an MCP server connection."""
        self.servers[name] = MCPClient(url)
        print(f"✓ Added MCP server: {name} ({url})")

    async def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """List tools from all registered servers."""
        all_tools = {}
        for name, server in self.servers.items():
            tools = await server.list_tools()
            all_tools[name] = tools
        return all_tools

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Call a tool on a specific server."""
        server = self.servers.get(server_name)
        if not server:
            print(f"MCP server {server_name} not found")
            return None

        return await server.call_tool(tool_name, arguments)

    async def shutdown(self):
        """Close all server connections."""
        for server in self.servers.values():
            await server.close()


# Global instance
mcp_manager = MCPManager()

# Example: Add MCP servers
# mcp_manager.add_server("archon", "http://localhost:3000")
# mcp_manager.add_server("custom", "http://localhost:3001")
