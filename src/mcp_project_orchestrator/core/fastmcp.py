#!/usr/bin/env python3
"""
Enhanced FastMCP server implementation for the MCP Project Orchestrator.

This module provides a comprehensive MCP server that handles communication
with MCP clients like Claude Desktop, exposing project orchestration,
prompt management, and diagram generation capabilities through the Model
Context Protocol.
"""
import os
import sys
import signal
import logging
import json
import asyncio
from typing import Dict, Any, Optional, Callable, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mcp-project-orchestrator")

class MCP_Error(Exception):
    """Base exception class for MCP server errors."""
    pass

class FastMCPServer:
    """
    Enhanced FastMCP server implementation for project orchestration.
    
    This class provides a comprehensive MCP server that handles communication
    with MCP clients, exposing orchestration capabilities through
    registered tools and resources with robust error handling.
    """
    
    def __init__(self, config):
        """
        Initialize the MCP server with the given configuration.
        
        Args:
            config: The server configuration object
        """
        self.name = config.name if hasattr(config, 'name') else "MCP Project Orchestrator"
        self.config = config
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.resources: Dict[str, Any] = {}
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        logger.info(f"Initialized FastMCP server '{self.name}'")
    
    async def initialize(self) -> None:
        """
        Initialize the server asynchronously.
        
        This method should be called after the server is created to set up
        all required components before starting the server.
        """
        logger.info("Initializing FastMCPServer")
        
        # Additional initialization logic can be added here
        
        logger.info("FastMCPServer initialization complete")
    
    async def start(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """
        Start the server asynchronously.
        
        Args:
            host: Optional host to bind to (overrides config)
            port: Optional port to bind to (overrides config)
        """
        # Use provided values or fall back to config
        self.host = host or self.config.host
        self.port = port or self.config.port
        
        logger.info(f"Starting FastMCP server on {self.host}:{self.port}")
        
        # Server startup logic would go here
        
        logger.info(f"FastMCP server started successfully on {self.host}:{self.port}")
    
    async def stop(self) -> None:
        """
        Stop the server gracefully.
        """
        logger.info("Stopping FastMCP server")
        
        # Server shutdown logic would go here
        
        logger.info("FastMCP server stopped")
    
    def tool(self, func: Optional[Callable] = None, 
             name: Optional[str] = None, 
             description: Optional[str] = None,
             parameters: Optional[Dict[str, Any]] = None):
        """
        Decorator to register a function as an MCP tool.
        
        Args:
            func: The function to register
            name: Optional name for the tool (defaults to function name)
            description: Optional description of the tool
            parameters: Optional parameters schema for the tool
        
        Returns:
            The decorated function
        """
        def decorator(fn):
            tool_name = name or fn.__name__
            tool_desc = description or fn.__doc__ or f"Tool {tool_name}"
            
            # Extract parameters from function signature if not provided
            tool_params = parameters or {}
            if not tool_params:
                import inspect
                sig = inspect.signature(fn)
                tool_params = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue
                        
                    param_type = "string"  # Default type
                    if param.annotation is not inspect.Parameter.empty:
                        if param.annotation == str:
                            param_type = "string"
                        elif param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == float:
                            param_type = "number"
                        elif param.annotation == bool:
                            param_type = "boolean"
                        elif param.annotation == dict or param.annotation == Dict:
                            param_type = "object"
                        elif param.annotation == list or param.annotation == List:
                            param_type = "array"
                    
                    tool_params["properties"][param_name] = {
                        "type": param_type,
                        "description": f"Parameter {param_name}"
                    }
                    
                    # Add to required params if no default value
                    if param.default is inspect.Parameter.empty:
                        tool_params["required"].append(param_name)
            
            self.tools[tool_name] = {
                "function": fn,
                "description": tool_desc,
                "parameters": tool_params
            }
            
            logger.info(f"Registered tool '{tool_name}'")
            return fn
        
        if func is None:
            return decorator
        return decorator(func)
    
    def resource(self, name: str, content: Any) -> None:
        """
        Register a resource with the MCP server.
        
        Args:
            name: Name of the resource
            content: Content of the resource
        """
        self.resources[name] = content
        logger.info(f"Registered resource '{name}'")
    
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable):
        """
        Register a tool with the MCP server.
        
        Args:
            name: Name of the tool
            description: Description of the tool
            parameters: Parameters schema for the tool
            handler: Handler function for the tool
        """
        logger.info(f"Registering tool: {name}")
        
        self.tools[name] = {
            "function": handler,
            "description": description,
            "parameters": parameters
        }
        
        logger.debug(f"Tool registered: {name} - {description}")
    
    def _handle_signal(self, signum: int, frame: Any) -> None:
        """
        Handle termination signals gracefully.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, shutting down...")
        
        # Create and run an asyncio task to stop the server
        loop = asyncio.get_event_loop()
        loop.create_task(self.stop())
        
        # Allow some time for cleanup
        loop.call_later(2, loop.stop)
    
    def _handle_client_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP protocol message from a client.
        
        Args:
            message: The message from the client
        
        Returns:
            The response to send back to the client
        """
        try:
            if "jsonrpc" not in message or message["jsonrpc"] != "2.0":
                return self._error_response(message.get("id"), -32600, "Invalid request")
            
            if "method" not in message:
                return self._error_response(message.get("id"), -32600, "Method not specified")
            
            method = message["method"]
            params = message.get("params", {})
            
            if method == "mcp/initialize":
                return self._handle_initialize(message["id"], params)
            elif method == "mcp/listTools":
                return self._handle_list_tools(message["id"])
            elif method == "mcp/callTool":
                return self._handle_call_tool(message["id"], params)
            elif method == "mcp/listResources":
                return self._handle_list_resources(message["id"])
            elif method == "mcp/readResource":
                return self._handle_read_resource(message["id"], params)
            else:
                return self._error_response(message["id"], -32601, f"Method '{method}' not supported")
        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return self._error_response(message.get("id"), -32603, f"Internal error: {str(e)}")
    
    def _error_response(self, id: Any, code: int, message: str) -> Dict[str, Any]:
        """
        Create an error response according to the JSON-RPC 2.0 spec.
        
        Args:
            id: The request ID
            code: The error code
            message: The error message
        
        Returns:
            The error response
        """
        return {
            "jsonrpc": "2.0",
            "id": id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    def _handle_initialize(self, id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the mcp/initialize method.
        
        Args:
            id: The request ID
            params: The method parameters
        
        Returns:
            The response
        """
        # Return server capabilities
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "name": self.name,
                "version": "0.1.0",
                "capabilities": {
                    "listTools": True,
                    "callTool": True,
                    "listResources": True,
                    "readResource": True
                }
            }
        }
    
    def _handle_list_tools(self, id: Any) -> Dict[str, Any]:
        """
        Handle the mcp/listTools method.
        
        Args:
            id: The request ID
        
        Returns:
            The response
        """
        tools = []
        for name, tool in self.tools.items():
            tools.append({
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"]
            })
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "tools": tools
            }
        }
    
    def _handle_call_tool(self, id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the mcp/callTool method.
        
        Args:
            id: The request ID
            params: The method parameters
        
        Returns:
            The response
        """
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        if not tool_name:
            return self._error_response(id, -32602, "Tool name not specified")
        
        if tool_name not in self.tools:
            return self._error_response(id, -32602, f"Tool '{tool_name}' not found")
        
        try:
            tool = self.tools[tool_name]["function"]
            result = tool(**tool_params)
            
            return {
                "jsonrpc": "2.0",
                "id": id,
                "result": {
                    "result": result
                }
            }
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {str(e)}")
            return self._error_response(id, -32603, f"Error calling tool '{tool_name}': {str(e)}")
    
    def _handle_list_resources(self, id: Any) -> Dict[str, Any]:
        """
        Handle the mcp/listResources method.
        
        Args:
            id: The request ID
        
        Returns:
            The response
        """
        resources = []
        for name in self.resources:
            resources.append({
                "uri": f"mcp://{self.name.lower()}/resources/{name}",
                "name": name
            })
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "resources": resources
            }
        }
    
    def _handle_read_resource(self, id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the mcp/readResource method.
        
        Args:
            id: The request ID
            params: The method parameters
        
        Returns:
            The response
        """
        uri = params.get("uri")
        if not uri:
            return self._error_response(id, -32602, "Resource URI not specified")
        
        # Parse the URI to get the resource name
        resource_name = uri.split("/")[-1]
        
        if resource_name not in self.resources:
            return self._error_response(id, -32602, f"Resource '{resource_name}' not found")
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "contents": self.resources[resource_name]
            }
        }
    
    def run(self, host: str = "127.0.0.1", port: int = 8080) -> None:
        """
        Run the MCP server and handle client connections.
        
        Args:
            host: The host to bind to
            port: The port to listen on
        """
        logger.info(f"FastMCP server '{self.name}' running with configuration: {self.config}")
        
        try:
            import asyncio
            import websockets
            
            async def handle_websocket(websocket: Any, path: str) -> None:
                """Handle a websocket connection."""
                async for message in websocket:
                    try:
                        request = json.loads(message)
                        logger.debug(f"Received message: {request}")
                        
                        response = self._handle_client_message(request)
                        logger.debug(f"Sending response: {response}")
                        
                        await websocket.send(json.dumps(response))
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding message: {str(e)}")
                        await websocket.send(json.dumps(self._error_response(None, -32700, "Parse error")))
                    except Exception as e:
                        logger.error(f"Error handling message: {str(e)}")
                        await websocket.send(json.dumps(self._error_response(None, -32603, f"Internal error: {str(e)}")))
            
            # Start the server
            start_server = websockets.serve(handle_websocket, host, port)
            asyncio.get_event_loop().run_until_complete(start_server)
            
            logger.info(f"Server running on {host}:{port}")
            logger.info("Press Ctrl+C to stop")
            
            # Keep the event loop running
            asyncio.get_event_loop().run_forever()
            
        except ImportError:
            # Fallback to stdio for compatibility with Claude Desktop
            logger.info("Websockets not available, falling back to stdio")
            self._run_stdio()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        except Exception as e:
            logger.error(f"Error running server: {str(e)}")
        finally:
            logger.info("Server shutting down")
    
    def _run_stdio(self) -> None:
        """Run the MCP server using standard input and output streams."""
        logger.info("Running in stdio mode")
        
        # Handle UTF-8 encoding on Windows
        if sys.platform == "win32":
            import msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
            sys.stdin = open(sys.stdin.fileno(), mode='r', encoding='utf-8', buffering=1)
        
        while True:
            try:
                # Read the content length header
                header = sys.stdin.readline().strip()
                if not header:
                    continue
                
                content_length = int(header.split(":")[1].strip())
                
                # Skip the empty line
                sys.stdin.readline()
                
                # Read the message content
                content = sys.stdin.read(content_length)
                
                # Parse and handle the message
                message = json.loads(content)
                response = self._handle_client_message(message)
                
                # Send the response
                response_json = json.dumps(response)
                response_bytes = response_json.encode('utf-8')
                sys.stdout.write(f"Content-Length: {len(response_bytes)}\r\n\r\n")
                sys.stdout.write(response_json)
                sys.stdout.flush()
                
            except Exception as e:
                logger.error(f"Error in stdio loop: {str(e)}")
                # Try to recover and continue

if __name__ == "__main__":
    import argparse
    from .config import MCPConfig

    parser = argparse.ArgumentParser(description="FastMCP Server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    
    args = parser.parse_args()
    
    # Create a config object
    config = MCPConfig(args.config) if args.config else MCPConfig()
    
    server = FastMCPServer(config)
    server.run(host=args.host, port=args.port) 