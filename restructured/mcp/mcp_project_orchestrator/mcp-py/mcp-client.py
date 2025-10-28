# client.py
import asyncio
import json
from typing import Any, Dict, List, Optional
import os
import httpx
from urllib.parse import urljoin

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import mcp.types as types

class MCPClient:
    """A flexible MCP client that supports both stdio and HTTP/SSE transports"""
    
    def __init__(self, transport_type: str = "stdio", server_url: Optional[str] = None):
        self.transport_type = transport_type
        self.server_url = server_url or "http://localhost:8000"
        self.session: Optional[ClientSession] = None
        self.http_client = httpx.AsyncClient()

    async def connect_stdio(self, server_command: str, server_args: Optional[List[str]] = None):
        """Connect using stdio transport"""
        params = StdioServerParameters(
            command=server_command,
            args=server_args or [],
            env=None
        )
        
        streams = await stdio_client(params).__aenter__()
        self.session = await ClientSession(streams[0], streams[1]).__aenter__()
        await self.session.initialize()

    async def connect_http(self):
        """Connect using HTTP transport"""
        # For HTTP transport, we don't need to maintain a persistent connection
        # We'll just make HTTP requests as needed
        pass

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        if self.transport_type == "stdio":
            if not self.session:
                raise RuntimeError("Not connected")
            response = await self.session.list_tools()
            return [tool.dict() for tool in response.tools]
        else:
            # Use HTTP endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(urljoin(self.server_url, "/tools"))
                response.raise_for_status()
                return response.json()["tools"]

    async def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Call a specific tool"""
        if self.transport_type == "stdio":
            if not self.session:
                raise RuntimeError("Not connected")
            result = await self.session.call_tool(tool_name, arguments or {})
            return result
        else:
            # Use HTTP endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    urljoin(self.server_url, f"/tools/call/{tool_name}"),
                    json=arguments or {}
                )
                response.raise_for_status()
                return response.json()["result"]

    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.__aexit__(None, None, None)
        await self.http_client.aclose()

class MCPClientCLI:
    """Command-line interface for the MCP client"""
    
    def __init__(self):
        self.transport_type = os.environ.get("MCP_TRANSPORT", "stdio")
        self.server_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8000")
        self.client = MCPClient(self.transport_type, self.server_url)

    async def run(self):
        """Run the CLI"""
        try:
            if self.transport_type == "stdio":
                await self.client.connect_stdio("python", ["server.py"])
            else:
                await self.client.connect_http()

            while True:
                command = input("\nEnter command (list_tools/call_tool/quit): ").strip()
                
                if command == "quit":
                    break
                elif command == "list_tools":
                    tools = await self.client.list_tools()
                    print("\nAvailable tools:")
                    for tool in tools:
                        print(f"- {tool['name']}: {tool['description']}")
                elif command == "call_tool":
                    tool_name = input("Enter tool name: ").strip()
                    args_str = input("Enter arguments as JSON (or empty): ").strip()
                    arguments = json.loads(args_str) if args_str else {}
                    
                    result = await self.client.call_tool(tool_name, arguments)
                    print("\nResult:", result)
                else:
                    print("Unknown command")

        finally:
            await self.client.close()

async def main():
    cli = MCPClientCLI()
    await cli.run()

if __name__ == "__main__":
    asyncio.run(main())
