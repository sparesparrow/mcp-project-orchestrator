"""
Main MCP Server implementation for PrintCast Agent.

This server orchestrates voice-to-print workflows, integrating multiple services:
- Asterisk SIP for telephony
- ElevenLabs for conversational AI
- GitHub/RSS for content sourcing
- CUPS for printing
- Delivery services for shipping
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel, Field
import structlog

from ..integrations.asterisk import AsteriskManager
from ..integrations.elevenlabs import ElevenLabsAgent
from ..integrations.content import ContentFetcher
from ..integrations.printing import PrintManager
from ..integrations.delivery import DeliveryService
from ..orchestration.workflow import WorkflowOrchestrator
from ..utils.monitoring import MetricsCollector

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class CallSession(BaseModel):
    """Represents an active call session."""
    
    session_id: str
    caller_id: str
    start_time: datetime
    selected_items: List[str] = Field(default_factory=list)
    delivery_address: Optional[str] = None
    status: str = "active"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PrintCastMCPServer:
    """
    Main MCP server for PrintCast Agent system.
    
    Provides tools and resources for:
    - Handling incoming calls through Asterisk
    - Managing AI voice conversations
    - Fetching and presenting content
    - Processing print jobs
    - Arranging delivery
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PrintCast MCP Server.
        
        Args:
            config: Configuration dictionary for all services
        """
        self.config = config or {}
        self.app = FastMCP("PrintCast Agent")
        self.sessions: Dict[str, CallSession] = {}
        
        # Initialize service managers
        self.asterisk = AsteriskManager(self.config.get("asterisk", {}))
        self.elevenlabs = ElevenLabsAgent(self.config.get("elevenlabs", {}))
        self.content = ContentFetcher(self.config.get("content", {}))
        self.printer = PrintManager(self.config.get("printing", {}))
        self.delivery = DeliveryService(self.config.get("delivery", {}))
        self.orchestrator = WorkflowOrchestrator(
            asterisk=self.asterisk,
            elevenlabs=self.elevenlabs,
            content=self.content,
            printer=self.printer,
            delivery=self.delivery
        )
        self.metrics = MetricsCollector()
        
        # Register MCP tools
        self._register_tools()
        
        # Register MCP resources
        self._register_resources()
        
        logger.info("PrintCast MCP Server initialized", config=self.config)
    
    def _register_tools(self):
        """Register all MCP tools."""
        
        @self.app.tool()
        async def handle_incoming_call(
            caller_id: str,
            dtmf_code: Optional[str] = None,
            language: str = "cs"
        ) -> Dict[str, Any]:
            """
            Handle an incoming call and initiate the voice workflow.
            
            Args:
                caller_id: The phone number of the caller
                dtmf_code: Optional DTMF code entered by caller
                language: Language preference (cs=Czech, en=English)
            
            Returns:
                Session information and next steps
            """
            try:
                # Create new session
                session = CallSession(
                    session_id=f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{caller_id}",
                    caller_id=caller_id,
                    start_time=datetime.now(),
                    metadata={"language": language, "dtmf_code": dtmf_code}
                )
                self.sessions[session.session_id] = session
                
                # Start voice agent
                agent_response = await self.elevenlabs.start_conversation(
                    session_id=session.session_id,
                    language=language
                )
                
                # Get initial content options
                content_options = await self.content.get_available_content()
                
                logger.info(
                    "Call session started",
                    session_id=session.session_id,
                    caller_id=caller_id
                )
                
                return {
                    "session_id": session.session_id,
                    "status": "connected",
                    "agent_ready": agent_response.get("ready", False),
                    "content_options": content_options,
                    "message": f"Welcome! Session {session.session_id} started."
                }
                
            except Exception as e:
                logger.error("Failed to handle incoming call", error=str(e))
                raise
        
        @self.app.tool()
        async def fetch_trending_content(
            content_type: str = "github",
            limit: int = 5,
            language: Optional[str] = None
        ) -> List[Dict[str, Any]]:
            """
            Fetch trending content from various sources.
            
            Args:
                content_type: Type of content (github, rss, news)
                limit: Maximum number of items to fetch
                language: Optional language filter
            
            Returns:
                List of trending content items
            """
            try:
                if content_type == "github":
                    items = await self.content.fetch_github_trending(
                        limit=limit,
                        language=language
                    )
                elif content_type == "rss":
                    items = await self.content.fetch_rss_feeds(limit=limit)
                elif content_type == "news":
                    items = await self.content.fetch_news(limit=limit)
                else:
                    raise ValueError(f"Unknown content type: {content_type}")
                
                logger.info(
                    "Fetched trending content",
                    type=content_type,
                    count=len(items)
                )
                
                return items
                
            except Exception as e:
                logger.error("Failed to fetch content", error=str(e))
                raise
        
        @self.app.tool()
        async def process_user_selection(
            session_id: str,
            selected_items: List[str],
            delivery_address: str,
            delivery_method: str = "post"
        ) -> Dict[str, Any]:
            """
            Process user's content selection and initiate print/delivery.
            
            Args:
                session_id: Active session ID
                selected_items: List of selected item IDs
                delivery_address: Delivery address
                delivery_method: Delivery method (post, courier)
            
            Returns:
                Order confirmation and tracking information
            """
            try:
                session = self.sessions.get(session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")
                
                # Update session
                session.selected_items = selected_items
                session.delivery_address = delivery_address
                
                # Orchestrate the workflow
                result = await self.orchestrator.process_order(
                    session_id=session_id,
                    selected_items=selected_items,
                    delivery_address=delivery_address,
                    delivery_method=delivery_method
                )
                
                # Update metrics
                await self.metrics.record_order(session_id, len(selected_items))
                
                logger.info(
                    "Order processed",
                    session_id=session_id,
                    items_count=len(selected_items),
                    tracking_id=result.get("tracking_id")
                )
                
                return result
                
            except Exception as e:
                logger.error("Failed to process selection", error=str(e))
                raise
        
        @self.app.tool()
        async def generate_print_preview(
            session_id: str,
            selected_items: List[str],
            format: str = "pdf"
        ) -> Dict[str, Any]:
            """
            Generate a print preview for selected items.
            
            Args:
                session_id: Active session ID
                selected_items: List of selected item IDs
                format: Output format (pdf, html)
            
            Returns:
                Preview file path and metadata
            """
            try:
                # Generate preview document
                preview = await self.printer.generate_preview(
                    items=selected_items,
                    format=format
                )
                
                logger.info(
                    "Print preview generated",
                    session_id=session_id,
                    format=format
                )
                
                return {
                    "preview_url": preview["url"],
                    "page_count": preview["pages"],
                    "file_size": preview["size"],
                    "format": format
                }
                
            except Exception as e:
                logger.error("Failed to generate preview", error=str(e))
                raise
        
        @self.app.tool()
        async def get_delivery_quote(
            delivery_address: str,
            delivery_method: str = "post",
            weight_grams: int = 100
        ) -> Dict[str, Any]:
            """
            Get delivery cost estimate.
            
            Args:
                delivery_address: Delivery address
                delivery_method: Delivery method
                weight_grams: Estimated weight in grams
            
            Returns:
                Delivery quote with pricing and timing
            """
            try:
                quote = await self.delivery.get_quote(
                    address=delivery_address,
                    method=delivery_method,
                    weight=weight_grams
                )
                
                return {
                    "price": quote["price"],
                    "currency": quote["currency"],
                    "estimated_delivery": quote["estimated_delivery"],
                    "carrier": quote["carrier"]
                }
                
            except Exception as e:
                logger.error("Failed to get delivery quote", error=str(e))
                raise
        
        @self.app.tool()
        async def end_call_session(
            session_id: str,
            reason: str = "completed"
        ) -> Dict[str, Any]:
            """
            End an active call session.
            
            Args:
                session_id: Session to end
                reason: Reason for ending (completed, cancelled, error)
            
            Returns:
                Session summary
            """
            try:
                session = self.sessions.get(session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")
                
                # Update session status
                session.status = reason
                
                # Stop voice agent
                await self.elevenlabs.end_conversation(session_id)
                
                # Generate session summary
                duration = (datetime.now() - session.start_time).total_seconds()
                
                summary = {
                    "session_id": session_id,
                    "duration_seconds": duration,
                    "items_selected": len(session.selected_items),
                    "status": reason,
                    "caller_id": session.caller_id
                }
                
                # Clean up session after delay
                asyncio.create_task(self._cleanup_session(session_id))
                
                logger.info("Call session ended", **summary)
                
                return summary
                
            except Exception as e:
                logger.error("Failed to end session", error=str(e))
                raise
    
    def _register_resources(self):
        """Register MCP resources for monitoring and configuration."""
        
        @self.app.resource("resource://sessions/active")
        async def get_active_sessions() -> str:
            """Get list of active call sessions."""
            active = [
                {
                    "session_id": s.session_id,
                    "caller_id": s.caller_id,
                    "start_time": s.start_time.isoformat(),
                    "status": s.status,
                    "items_selected": len(s.selected_items)
                }
                for s in self.sessions.values()
                if s.status == "active"
            ]
            return json.dumps(active, indent=2)
        
        @self.app.resource("resource://config/services")
        async def get_service_config() -> str:
            """Get current service configuration."""
            config = {
                "asterisk": {
                    "enabled": self.asterisk.is_connected(),
                    "host": self.config.get("asterisk", {}).get("host", "localhost")
                },
                "elevenlabs": {
                    "enabled": self.elevenlabs.is_configured(),
                    "model": self.config.get("elevenlabs", {}).get("model", "eleven_multilingual_v2")
                },
                "printing": {
                    "enabled": self.printer.is_available(),
                    "printer": self.config.get("printing", {}).get("default_printer", "default")
                },
                "delivery": {
                    "enabled": self.delivery.is_configured(),
                    "carriers": self.config.get("delivery", {}).get("carriers", [])
                }
            }
            return json.dumps(config, indent=2)
        
        @self.app.resource("resource://metrics/daily")
        async def get_daily_metrics() -> str:
            """Get daily usage metrics."""
            metrics = await self.metrics.get_daily_stats()
            return json.dumps(metrics, indent=2)
    
    async def _cleanup_session(self, session_id: str, delay: int = 300):
        """
        Clean up session data after delay.
        
        Args:
            session_id: Session to clean up
            delay: Delay in seconds before cleanup
        """
        await asyncio.sleep(delay)
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info("Session cleaned up", session_id=session_id)
    
    async def start(self):
        """Start the MCP server and all services."""
        try:
            # Initialize all services
            await self.asterisk.connect()
            await self.elevenlabs.initialize()
            await self.printer.initialize()
            await self.delivery.initialize()
            
            # Start metrics collection
            asyncio.create_task(self.metrics.start_collection())
            
            # Start the MCP server
            logger.info("Starting PrintCast MCP Server")
            await self.app.run()
            
        except Exception as e:
            logger.error("Failed to start server", error=str(e))
            raise
    
    async def stop(self):
        """Stop the MCP server and cleanup."""
        try:
            # End all active sessions
            for session_id in list(self.sessions.keys()):
                await self.end_call_session(session_id, reason="shutdown")
            
            # Disconnect services
            await self.asterisk.disconnect()
            await self.elevenlabs.shutdown()
            await self.printer.shutdown()
            await self.delivery.shutdown()
            
            logger.info("PrintCast MCP Server stopped")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
            raise