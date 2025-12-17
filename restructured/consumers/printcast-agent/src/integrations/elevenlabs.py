"""
ElevenLabs Conversational AI integration for PrintCast Agent.

Provides voice synthesis and conversation management using ElevenLabs API.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
import base64

import httpx
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ConversationState(BaseModel):
    """State of an active conversation."""
    
    session_id: str
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    language: str = "cs"
    is_active: bool = False
    start_time: datetime = Field(default_factory=datetime.now)
    transcript: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ElevenLabsAgent:
    """
    Manages ElevenLabs Conversational AI integration.
    
    Features:
    - Multi-language TTS/STT
    - Real-time conversation handling
    - Voice cloning support
    - Custom prompts and behaviors
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ElevenLabs agent.
        
        Args:
            config: Configuration including:
                - api_key: ElevenLabs API key
                - agent_id: Pre-configured agent ID (optional)
                - voice_id: Voice ID for TTS
                - model: TTS model (eleven_multilingual_v2)
                - websocket_url: WebSocket endpoint
        """
        self.config = config
        self.api_key = config.get("api_key", "")
        self.agent_id = config.get("agent_id")
        self.voice_id = config.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # Default voice
        self.model = config.get("model", "eleven_multilingual_v2")
        self.base_url = config.get("base_url", "https://api.elevenlabs.io/v1")
        self.ws_url = config.get("websocket_url", "wss://api.elevenlabs.io/v1/convai/conversation")
        
        self.client: Optional[httpx.AsyncClient] = None
        self.conversations: Dict[str, ConversationState] = {}
        self.websockets: Dict[str, Any] = {}
        
        logger.info(
            "ElevenLabs agent initialized",
            voice_id=self.voice_id,
            model=self.model
        )
    
    async def initialize(self):
        """Initialize HTTP client and verify API access."""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            # Verify API access
            response = await self.client.get("/user")
            if response.status_code == 200:
                user_info = response.json()
                logger.info(
                    "ElevenLabs API connected",
                    subscription=user_info.get("subscription", {}).get("tier")
                )
            else:
                logger.warning("ElevenLabs API verification failed", status=response.status_code)
                
        except Exception as e:
            logger.error("Failed to initialize ElevenLabs client", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown client and cleanup."""
        try:
            # End all active conversations
            for session_id in list(self.conversations.keys()):
                await self.end_conversation(session_id)
            
            # Close HTTP client
            if self.client:
                await self.client.aclose()
            
            logger.info("ElevenLabs agent shutdown")
            
        except Exception as e:
            logger.error("Error during ElevenLabs shutdown", error=str(e))
    
    def is_configured(self) -> bool:
        """Check if agent is properly configured."""
        return bool(self.api_key and self.client)
    
    async def start_conversation(
        self,
        session_id: str,
        language: str = "cs",
        initial_prompt: Optional[str] = None,
        voice_settings: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Start a new conversation session.
        
        Args:
            session_id: Unique session identifier
            language: Conversation language
            initial_prompt: Optional initial system prompt
            voice_settings: Voice configuration (stability, similarity_boost)
        
        Returns:
            Conversation initialization result
        """
        try:
            # Create conversation state
            state = ConversationState(
                session_id=session_id,
                language=language,
                is_active=True
            )
            
            # Prepare conversation configuration
            config = {
                "agent_id": self.agent_id,
                "conversation": {
                    "conversation_id": f"conv_{session_id}",
                    "variables": {
                        "language": language,
                        "session_id": session_id
                    }
                }
            }
            
            if initial_prompt:
                config["conversation"]["initial_prompt"] = initial_prompt
            
            if voice_settings:
                config["voice_settings"] = voice_settings
            else:
                config["voice_settings"] = {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            
            # Start conversation via API
            if self.agent_id:
                response = await self.client.post(
                    f"/convai/agents/{self.agent_id}/conversation",
                    json=config
                )
                
                if response.status_code == 200:
                    result = response.json()
                    state.conversation_id = result.get("conversation_id")
                    state.agent_id = self.agent_id
                    
                    logger.info(
                        "Conversation started",
                        session_id=session_id,
                        conversation_id=state.conversation_id
                    )
                else:
                    logger.error(
                        "Failed to start conversation",
                        status=response.status_code,
                        error=response.text
                    )
                    raise RuntimeError(f"Failed to start conversation: {response.text}")
            
            self.conversations[session_id] = state
            
            return {
                "ready": True,
                "session_id": session_id,
                "conversation_id": state.conversation_id,
                "language": language
            }
            
        except Exception as e:
            logger.error("Failed to start conversation", error=str(e))
            raise
    
    async def send_message(
        self,
        session_id: str,
        text: str,
        voice_response: bool = True
    ) -> Dict[str, Any]:
        """
        Send a text message to the conversation.
        
        Args:
            session_id: Session identifier
            text: Message text
            voice_response: Whether to generate voice response
        
        Returns:
            Response from the agent
        """
        state = self.conversations.get(session_id)
        if not state or not state.is_active:
            raise ValueError(f"No active conversation for session {session_id}")
        
        try:
            # Add to transcript
            state.transcript.append({
                "role": "user",
                "content": text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Send to conversation API
            if state.conversation_id:
                response = await self.client.post(
                    f"/convai/conversations/{state.conversation_id}/message",
                    json={
                        "text": text,
                        "voice_response": voice_response
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Add response to transcript
                    state.transcript.append({
                        "role": "assistant",
                        "content": result.get("text", ""),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    return {
                        "text": result.get("text"),
                        "audio": result.get("audio"),
                        "metadata": result.get("metadata", {})
                    }
                else:
                    logger.error(
                        "Failed to send message",
                        status=response.status_code,
                        error=response.text
                    )
                    raise RuntimeError(f"Failed to send message: {response.text}")
            
            # Fallback to TTS if no conversation ID
            return await self.text_to_speech(text, language=state.language)
            
        except Exception as e:
            logger.error("Failed to send message", error=str(e))
            raise
    
    async def text_to_speech(
        self,
        text: str,
        language: str = "cs",
        voice_id: Optional[str] = None,
        output_format: str = "mp3_44100_128"
    ) -> Dict[str, Any]:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert
            language: Language code
            voice_id: Optional voice ID override
            output_format: Audio format
        
        Returns:
            Audio data and metadata
        """
        try:
            voice = voice_id or self.voice_id
            
            # Prepare TTS request
            request_data = {
                "text": text,
                "model_id": self.model,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            # Language-specific adjustments
            if language == "cs":
                request_data["language_code"] = "cs-CZ"
            elif language == "en":
                request_data["language_code"] = "en-US"
            
            response = await self.client.post(
                f"/text-to-speech/{voice}",
                json=request_data,
                headers={"Accept": f"audio/{output_format.split('_')[0]}"}
            )
            
            if response.status_code == 200:
                audio_data = response.content
                
                return {
                    "audio": base64.b64encode(audio_data).decode("utf-8"),
                    "format": output_format,
                    "duration_estimate": len(text) * 0.15,  # Rough estimate
                    "size_bytes": len(audio_data)
                }
            else:
                logger.error(
                    "TTS failed",
                    status=response.status_code,
                    error=response.text
                )
                raise RuntimeError(f"TTS failed: {response.text}")
                
        except Exception as e:
            logger.error("Failed to generate speech", error=str(e))
            raise
    
    async def generate_content_summary(
        self,
        items: List[Dict[str, Any]],
        language: str = "cs",
        max_items: int = 5
    ) -> str:
        """
        Generate a voice-friendly summary of content items.
        
        Args:
            items: List of content items
            language: Target language
            max_items: Maximum items to include
        
        Returns:
            Formatted summary text for TTS
        """
        try:
            # Limit items
            items = items[:max_items]
            
            # Generate summary based on language
            if language == "cs":
                summary = "Zde jsou nejnovější trendy:\n\n"
                for i, item in enumerate(items, 1):
                    title = item.get("title", item.get("name", ""))
                    description = item.get("description", "")[:100]
                    
                    summary += f"Číslo {i}: {title}. "
                    if description:
                        summary += f"{description}... "
                    summary += "\n"
                
                summary += "\nŘekněte čísla položek, které chcete vytisknout."
                
            else:  # English default
                summary = "Here are the latest trends:\n\n"
                for i, item in enumerate(items, 1):
                    title = item.get("title", item.get("name", ""))
                    description = item.get("description", "")[:100]
                    
                    summary += f"Number {i}: {title}. "
                    if description:
                        summary += f"{description}... "
                    summary += "\n"
                
                summary += "\nPlease say the numbers of items you'd like to print."
            
            return summary
            
        except Exception as e:
            logger.error("Failed to generate summary", error=str(e))
            return "Error generating summary"
    
    async def process_user_selection(
        self,
        session_id: str,
        audio_data: Optional[bytes] = None,
        dtmf_input: Optional[str] = None
    ) -> List[int]:
        """
        Process user's selection from audio or DTMF.
        
        Args:
            session_id: Session identifier
            audio_data: Optional audio input for STT
            dtmf_input: Optional DTMF digits
        
        Returns:
            List of selected item indices
        """
        try:
            selected = []
            
            if dtmf_input:
                # Parse DTMF digits
                for digit in dtmf_input:
                    if digit.isdigit():
                        num = int(digit)
                        if 1 <= num <= 9:
                            selected.append(num)
            
            elif audio_data:
                # Perform speech-to-text
                transcript = await self.speech_to_text(audio_data)
                
                # Parse transcript for numbers
                # Simple implementation - could be enhanced with NLP
                words = transcript.lower().split()
                number_words = {
                    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                    "jedna": 1, "dva": 2, "tři": 3, "čtyři": 4, "pět": 5,
                    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5
                }
                
                for word in words:
                    if word in number_words:
                        selected.append(number_words[word])
                    elif word.isdigit():
                        num = int(word)
                        if 1 <= num <= 9:
                            selected.append(num)
            
            # Remove duplicates while preserving order
            selected = list(dict.fromkeys(selected))
            
            logger.info(
                "User selection processed",
                session_id=session_id,
                selected=selected
            )
            
            return selected
            
        except Exception as e:
            logger.error("Failed to process selection", error=str(e))
            return []
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        language: str = "cs"
    ) -> str:
        """
        Convert speech to text.
        
        Args:
            audio_data: Audio data
            language: Language code
        
        Returns:
            Transcribed text
        """
        try:
            # Note: ElevenLabs doesn't provide STT directly
            # This would integrate with another service like OpenAI Whisper
            # For now, returning placeholder
            
            logger.warning("STT not fully implemented - using placeholder")
            return "jedna a tři"  # Placeholder
            
        except Exception as e:
            logger.error("Failed to transcribe speech", error=str(e))
            return ""
    
    async def end_conversation(self, session_id: str) -> Dict[str, Any]:
        """
        End a conversation session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Conversation summary
        """
        state = self.conversations.get(session_id)
        if not state:
            return {"error": "Conversation not found"}
        
        try:
            # Mark as inactive
            state.is_active = False
            
            # End conversation via API if active
            if state.conversation_id and self.client:
                await self.client.post(
                    f"/convai/conversations/{state.conversation_id}/end"
                )
            
            # Close WebSocket if exists
            if session_id in self.websockets:
                ws = self.websockets[session_id]
                await ws.close()
                del self.websockets[session_id]
            
            # Generate summary
            duration = (datetime.now() - state.start_time).total_seconds()
            summary = {
                "session_id": session_id,
                "duration_seconds": duration,
                "messages_count": len(state.transcript),
                "language": state.language
            }
            
            # Clean up
            del self.conversations[session_id]
            
            logger.info("Conversation ended", **summary)
            
            return summary
            
        except Exception as e:
            logger.error("Failed to end conversation", error=str(e))
            return {"error": str(e)}
    
    def get_conversation_transcript(
        self,
        session_id: str
    ) -> List[Dict[str, str]]:
        """Get conversation transcript."""
        state = self.conversations.get(session_id)
        return state.transcript if state else []
    
    async def create_custom_agent(
        self,
        name: str,
        prompt: str,
        voice_id: str,
        language: str = "cs",
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Create a custom conversational agent.
        
        Args:
            name: Agent name
            prompt: System prompt
            voice_id: Voice to use
            language: Primary language
            tools: Optional tools/functions
        
        Returns:
            Agent ID
        """
        try:
            agent_config = {
                "name": name,
                "prompt": prompt,
                "voice_id": voice_id,
                "language": language,
                "first_message": self._get_greeting(language),
                "tools": tools or []
            }
            
            response = await self.client.post(
                "/convai/agents",
                json=agent_config
            )
            
            if response.status_code == 201:
                result = response.json()
                agent_id = result.get("agent_id")
                
                logger.info(
                    "Custom agent created",
                    agent_id=agent_id,
                    name=name
                )
                
                return agent_id
            else:
                logger.error(
                    "Failed to create agent",
                    status=response.status_code,
                    error=response.text
                )
                raise RuntimeError(f"Failed to create agent: {response.text}")
                
        except Exception as e:
            logger.error("Failed to create custom agent", error=str(e))
            raise
    
    def _get_greeting(self, language: str) -> str:
        """Get language-specific greeting."""
        greetings = {
            "cs": "Dobrý den! Jsem váš asistent PrintCast. Mohu vám přečíst nejnovější trendy a pomoci s jejich tiskem a doručením. Co by vás zajímalo?",
            "en": "Hello! I'm your PrintCast assistant. I can read you the latest trends and help with printing and delivery. What would you like to explore?",
        }
        return greetings.get(language, greetings["en"])