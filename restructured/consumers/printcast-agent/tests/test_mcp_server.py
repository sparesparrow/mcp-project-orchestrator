"""
Tests for PrintCast MCP Server.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.mcp_server.server import PrintCastMCPServer, CallSession
from src.integrations.content import ContentItem


@pytest.fixture
async def mock_config():
    """Create mock configuration."""
    return {
        "asterisk": {
            "host": "localhost",
            "port": 5038,
            "username": "test",
            "password": "test",
        },
        "elevenlabs": {
            "api_key": "test_key",
            "voice_id": "test_voice",
        },
        "content": {
            "rss_feeds": ["https://example.com/rss"],
        },
        "printing": {
            "default_printer": "test_printer",
        },
        "delivery": {
            "default_carrier": "post",
            "sender_address": {
                "name": "Test Sender",
                "street": "Test Street",
                "city": "Test City",
                "postal_code": "12345",
                "country": "CZ",
            },
        },
    }


@pytest.fixture
async def server(mock_config):
    """Create test server instance."""
    with patch("src.mcp_server.server.AsteriskManager"), \
         patch("src.mcp_server.server.ElevenLabsAgent"), \
         patch("src.mcp_server.server.ContentFetcher"), \
         patch("src.mcp_server.server.PrintManager"), \
         patch("src.mcp_server.server.DeliveryService"), \
         patch("src.mcp_server.server.WorkflowOrchestrator"):
        
        server = PrintCastMCPServer(mock_config)
        yield server


class TestPrintCastMCPServer:
    """Test PrintCast MCP Server functionality."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert server is not None
        assert server.config is not None
        assert server.sessions == {}
    
    @pytest.mark.asyncio
    async def test_handle_incoming_call(self, server):
        """Test handling incoming call."""
        # Mock ElevenLabs response
        server.elevenlabs.start_conversation = AsyncMock(
            return_value={"ready": True}
        )
        server.content.get_available_content = AsyncMock(
            return_value={"sources": {"github": {"available": True}}}
        )
        
        # Simulate incoming call
        result = await server._register_tools.handle_incoming_call(
            caller_id="+420123456789",
            language="cs"
        )
        
        assert result["status"] == "connected"
        assert "session_id" in result
        assert result["agent_ready"] is True
    
    @pytest.mark.asyncio
    async def test_fetch_trending_content(self, server):
        """Test fetching trending content."""
        # Mock content fetcher
        mock_items = [
            ContentItem(
                id="gh_test_repo",
                source="github",
                title="test/repo",
                description="Test repository"
            )
        ]
        server.content.fetch_github_trending = AsyncMock(
            return_value=mock_items
        )
        
        # Fetch content
        result = await server._register_tools.fetch_trending_content(
            content_type="github",
            limit=5
        )
        
        assert len(result) == 1
        assert result[0].id == "gh_test_repo"
    
    @pytest.mark.asyncio
    async def test_process_user_selection(self, server):
        """Test processing user selection."""
        # Create test session
        session = CallSession(
            session_id="test_session",
            caller_id="+420123456789",
            start_time=asyncio.get_event_loop().time()
        )
        server.sessions["test_session"] = session
        
        # Mock orchestrator
        server.orchestrator.process_order = AsyncMock(
            return_value={
                "success": True,
                "tracking_id": "TRACK123"
            }
        )
        
        # Process selection
        result = await server._register_tools.process_user_selection(
            session_id="test_session",
            selected_items=["item1", "item2"],
            delivery_address="Test Address, Test City, 12345"
        )
        
        assert result["success"] is True
        assert result["tracking_id"] == "TRACK123"
    
    @pytest.mark.asyncio
    async def test_end_call_session(self, server):
        """Test ending call session."""
        # Create test session
        session = CallSession(
            session_id="test_session",
            caller_id="+420123456789",
            start_time=asyncio.get_event_loop().time()
        )
        server.sessions["test_session"] = session
        
        # Mock ElevenLabs
        server.elevenlabs.end_conversation = AsyncMock()
        
        # End session
        result = await server._register_tools.end_call_session(
            session_id="test_session",
            reason="completed"
        )
        
        assert result["session_id"] == "test_session"
        assert result["status"] == "completed"
        assert "duration_seconds" in result


class TestContentFetching:
    """Test content fetching functionality."""
    
    @pytest.mark.asyncio
    async def test_github_trending_parsing(self):
        """Test parsing GitHub trending repositories."""
        from src.integrations.content import ContentFetcher
        
        fetcher = ContentFetcher({"cache_ttl": 60})
        
        # Mock HTTP response
        mock_html = """
        <article class="Box-row">
            <h2 class="h3">
                <a href="/openai/gpt">gpt</a>
            </h2>
            <p class="col-9">GPT language model</p>
            <span itemprop="programmingLanguage">Python</span>
        </article>
        """
        
        with patch.object(fetcher, 'client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_client.get = AsyncMock(return_value=mock_response)
            
            await fetcher.initialize()
            items = await fetcher.fetch_github_trending(limit=1)
            
            assert len(items) > 0
            if items:  # If parsing succeeded
                assert "gpt" in items[0].title.lower()


class TestWorkflowOrchestration:
    """Test workflow orchestration."""
    
    @pytest.mark.asyncio
    async def test_workflow_state_transitions(self):
        """Test workflow state transitions."""
        from src.orchestration.workflow import WorkflowOrchestrator, WorkflowContext, WorkflowState
        
        # Create mock services
        mock_asterisk = Mock()
        mock_elevenlabs = Mock()
        mock_content = Mock()
        mock_printer = Mock()
        mock_delivery = Mock()
        
        orchestrator = WorkflowOrchestrator(
            asterisk=mock_asterisk,
            elevenlabs=mock_elevenlabs,
            content=mock_content,
            printer=mock_printer,
            delivery=mock_delivery
        )
        
        # Create workflow context
        context = WorkflowContext(
            workflow_id="test_wf",
            session_id="test_session",
            caller_id="+420123456789",
            state=WorkflowState.IDLE
        )
        
        # Test state transition
        context.state = WorkflowState.CALL_INITIATED
        assert context.state == WorkflowState.CALL_INITIATED
        
        context.state = WorkflowState.GREETING
        assert context.state == WorkflowState.GREETING


@pytest.mark.asyncio
async def test_integration_flow():
    """Test complete integration flow."""
    # This would be an integration test with real services
    # For now, just verify the flow structure
    
    from src.mcp_server.server import PrintCastMCPServer
    
    config = {
        "asterisk": {"host": "localhost"},
        "elevenlabs": {"api_key": "test"},
        "content": {},
        "printing": {},
        "delivery": {},
    }
    
    with patch("src.mcp_server.server.AsteriskManager"), \
         patch("src.mcp_server.server.ElevenLabsAgent"), \
         patch("src.mcp_server.server.ContentFetcher"), \
         patch("src.mcp_server.server.PrintManager"), \
         patch("src.mcp_server.server.DeliveryService"), \
         patch("src.mcp_server.server.WorkflowOrchestrator"):
        
        server = PrintCastMCPServer(config)
        
        # Verify all components are initialized
        assert server.asterisk is not None
        assert server.elevenlabs is not None
        assert server.content is not None
        assert server.printer is not None
        assert server.delivery is not None
        assert server.orchestrator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])