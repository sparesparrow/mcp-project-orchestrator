# server.py
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPToolServer(Server):
    def __init__(self):
        super().__init__("tool-server")
        self.tools: List[Dict[str, Any]] = []
        self.load_tools()
        
    def load_tools(self):
        """Load tool definitions from tools.json"""
        try:
            with open("tools.json", "r") as f:
                self.tools = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load tools.json: {e}")
            self.tools = []

    async def handle_list_tools(self) -> List[types.Tool]:
        """Handle tools/list request"""
        return [
            types.Tool(
                name=tool["name"],
                description=tool.get("description", ""),
                inputSchema=tool["input_schema"]
            )
            for tool in self.tools
        ]

    async def handle_call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> List[types.TextContent]:
        """Handle tools/call request"""
        # Find the requested tool
        tool = next((t for t in self.tools if t["name"] == name), None)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        # Here you would implement the actual tool execution logic
        # For now, we'll just echo back the call details
        result = f"Called tool {name} with arguments: {json.dumps(arguments or {})}"
        
        return [types.TextContent(type="text", text=result)]

class TransportManager:
    """Manages different transport types for the MCP server"""
    def __init__(self, server: MCPToolServer):
        self.server = server
        self.app = FastAPI()
        self.setup_routes()

    def setup_routes(self):
        """Set up FastAPI routes for SSE and HTTP endpoints"""
        @self.app.get("/sse")
        async def sse_endpoint(request: Request):
            transport = SseServerTransport("/message")
            return EventSourceResponse(self.handle_sse(transport, request))

        @self.app.post("/message")
        async def message_endpoint(request: Request):
            message = await request.json()
            # Handle incoming messages for SSE transport
            return JSONResponse({"status": "ok"})

        @self.app.post("/tools/call/{tool_name}")
        async def call_tool(tool_name: str, request: Request):
            arguments = await request.json()
            result = await self.server.handle_call_tool(tool_name, arguments)
            return JSONResponse({"result": result})

        @self.app.get("/tools")
        async def list_tools():
            tools = await self.server.handle_list_tools()
            return JSONResponse({"tools": [t.dict() for t in tools]})

    async def handle_sse(self, transport, request):
        """Handle SSE connection"""
        async with transport.connect_sse(request.scope, request.receive, request.send) as streams:
            await self.server.run(
                streams[0],
                streams[1],
                self.server.create_initialization_options()
            )

    async def run_stdio(self):
        """Run server with stdio transport"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    # Create server and transport manager
    server = MCPToolServer()
    transport_mgr = TransportManager(server)

    # Determine transport type from environment
    transport_type = os.environ.get("MCP_TRANSPORT", "stdio")
    
    if transport_type == "stdio":
        await transport_mgr.run_stdio()
    else:
        # Run HTTP/SSE server
        port = int(os.environ.get("MCP_PORT", 8000))
        config = uvicorn.Config(transport_mgr.app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
