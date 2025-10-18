"""
Asterisk SIP integration for PrintCast Agent.

Handles telephony operations including:
- Call routing and management
- IVR interactions
- DTMF processing
- Call recording
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

import structlog
from panoramisk import Manager
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CallInfo(BaseModel):
    """Information about an active call."""
    
    channel: str
    caller_id: str
    called_number: str
    start_time: datetime
    state: str
    unique_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AsteriskManager:
    """
    Manages Asterisk SIP server integration.
    
    Provides high-level interface for:
    - AMI (Asterisk Manager Interface) operations
    - Call control and routing
    - IVR menu handling
    - DTMF input processing
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Asterisk manager.
        
        Args:
            config: Asterisk configuration including:
                - host: Asterisk server hostname
                - port: AMI port (default 5038)
                - username: AMI username
                - password: AMI password
                - context: Default dialplan context
        """
        self.config = config
        self.ami: Optional[Manager] = None
        self.connected = False
        self.active_calls: Dict[str, CallInfo] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Configuration
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 5038)
        self.username = config.get("username", "admin")
        self.password = config.get("password", "")
        self.context = config.get("context", "printcast-ivr")
        
        logger.info(
            "Asterisk manager initialized",
            host=self.host,
            port=self.port,
            context=self.context
        )
    
    async def connect(self) -> bool:
        """
        Connect to Asterisk AMI.
        
        Returns:
            True if connection successful
        """
        try:
            self.ami = Manager(
                host=self.host,
                port=self.port,
                username=self.username,
                secret=self.password
            )
            
            # Connect to AMI
            await self.ami.connect()
            
            # Register event handlers
            self.ami.register_event("*", self._handle_ami_event)
            
            self.connected = True
            logger.info("Connected to Asterisk AMI", host=self.host)
            
            return True
            
        except Exception as e:
            logger.error("Failed to connect to Asterisk", error=str(e))
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Asterisk AMI."""
        if self.ami and self.connected:
            try:
                await self.ami.logoff()
                await self.ami.close()
                self.connected = False
                logger.info("Disconnected from Asterisk")
            except Exception as e:
                logger.error("Error disconnecting from Asterisk", error=str(e))
    
    def is_connected(self) -> bool:
        """Check if connected to Asterisk."""
        return self.connected
    
    async def _handle_ami_event(self, event: Dict[str, Any]):
        """
        Handle AMI events.
        
        Args:
            event: AMI event data
        """
        event_type = event.get("Event", "")
        
        try:
            # Handle specific events
            if event_type == "Newchannel":
                await self._handle_new_channel(event)
            elif event_type == "Hangup":
                await self._handle_hangup(event)
            elif event_type == "DTMF":
                await self._handle_dtmf(event)
            elif event_type == "NewCallerid":
                await self._handle_caller_id(event)
            
            # Call registered handlers
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    asyncio.create_task(handler(event))
                    
        except Exception as e:
            logger.error(
                "Error handling AMI event",
                event_type=event_type,
                error=str(e)
            )
    
    async def _handle_new_channel(self, event: Dict[str, Any]):
        """Handle new channel creation."""
        channel = event.get("Channel", "")
        caller_id = event.get("CallerIDNum", "")
        unique_id = event.get("Uniqueid", "")
        
        call_info = CallInfo(
            channel=channel,
            caller_id=caller_id,
            called_number=event.get("Exten", ""),
            start_time=datetime.now(),
            state="ringing",
            unique_id=unique_id
        )
        
        self.active_calls[unique_id] = call_info
        
        logger.info(
            "New call detected",
            channel=channel,
            caller_id=caller_id,
            unique_id=unique_id
        )
    
    async def _handle_hangup(self, event: Dict[str, Any]):
        """Handle call hangup."""
        unique_id = event.get("Uniqueid", "")
        
        if unique_id in self.active_calls:
            call_info = self.active_calls[unique_id]
            duration = (datetime.now() - call_info.start_time).total_seconds()
            
            logger.info(
                "Call ended",
                unique_id=unique_id,
                duration=duration,
                caller_id=call_info.caller_id
            )
            
            del self.active_calls[unique_id]
    
    async def _handle_dtmf(self, event: Dict[str, Any]):
        """Handle DTMF digit press."""
        digit = event.get("Digit", "")
        unique_id = event.get("Uniqueid", "")
        
        if unique_id in self.active_calls:
            call_info = self.active_calls[unique_id]
            
            # Store DTMF in metadata
            if "dtmf_buffer" not in call_info.metadata:
                call_info.metadata["dtmf_buffer"] = ""
            
            call_info.metadata["dtmf_buffer"] += digit
            
            logger.debug(
                "DTMF received",
                digit=digit,
                unique_id=unique_id,
                buffer=call_info.metadata["dtmf_buffer"]
            )
    
    async def _handle_caller_id(self, event: Dict[str, Any]):
        """Handle caller ID update."""
        unique_id = event.get("Uniqueid", "")
        caller_id = event.get("CallerIDNum", "")
        
        if unique_id in self.active_calls:
            self.active_calls[unique_id].caller_id = caller_id
    
    async def originate_call(
        self,
        destination: str,
        caller_id: str = "PrintCast",
        timeout: int = 30,
        variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Originate an outbound call.
        
        Args:
            destination: Destination number
            caller_id: Caller ID to present
            timeout: Call timeout in seconds
            variables: Channel variables to set
        
        Returns:
            Call result information
        """
        if not self.connected:
            raise RuntimeError("Not connected to Asterisk")
        
        try:
            response = await self.ami.send_action({
                "Action": "Originate",
                "Channel": f"SIP/{destination}",
                "Context": self.context,
                "Exten": "s",
                "Priority": "1",
                "CallerID": caller_id,
                "Timeout": str(timeout * 1000),
                "Variable": variables or {}
            })
            
            logger.info(
                "Call originated",
                destination=destination,
                caller_id=caller_id
            )
            
            return {
                "success": response.get("Response") == "Success",
                "message": response.get("Message", ""),
                "action_id": response.get("ActionID", "")
            }
            
        except Exception as e:
            logger.error("Failed to originate call", error=str(e))
            raise
    
    async def transfer_call(
        self,
        channel: str,
        destination: str,
        context: Optional[str] = None
    ) -> bool:
        """
        Transfer an active call.
        
        Args:
            channel: Channel to transfer
            destination: Transfer destination
            context: Optional context (uses default if not specified)
        
        Returns:
            True if transfer successful
        """
        if not self.connected:
            raise RuntimeError("Not connected to Asterisk")
        
        try:
            response = await self.ami.send_action({
                "Action": "Redirect",
                "Channel": channel,
                "Context": context or self.context,
                "Exten": destination,
                "Priority": "1"
            })
            
            success = response.get("Response") == "Success"
            
            logger.info(
                "Call transferred",
                channel=channel,
                destination=destination,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error("Failed to transfer call", error=str(e))
            return False
    
    async def hangup_call(self, channel: str, cause: int = 16) -> bool:
        """
        Hangup an active call.
        
        Args:
            channel: Channel to hangup
            cause: Hangup cause code (16 = normal clearing)
        
        Returns:
            True if hangup successful
        """
        if not self.connected:
            raise RuntimeError("Not connected to Asterisk")
        
        try:
            response = await self.ami.send_action({
                "Action": "Hangup",
                "Channel": channel,
                "Cause": str(cause)
            })
            
            success = response.get("Response") == "Success"
            
            logger.info(
                "Call hangup requested",
                channel=channel,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error("Failed to hangup call", error=str(e))
            return False
    
    async def play_audio(
        self,
        channel: str,
        audio_file: str,
        interrupt_dtmf: bool = True
    ) -> bool:
        """
        Play audio file to channel.
        
        Args:
            channel: Channel to play audio to
            audio_file: Path to audio file
            interrupt_dtmf: Allow DTMF to interrupt playback
        
        Returns:
            True if playback started
        """
        if not self.connected:
            raise RuntimeError("Not connected to Asterisk")
        
        try:
            response = await self.ami.send_action({
                "Action": "Playback",
                "Channel": channel,
                "Filename": audio_file,
                "Interrupt": "yes" if interrupt_dtmf else "no"
            })
            
            success = response.get("Response") == "Success"
            
            logger.info(
                "Audio playback started",
                channel=channel,
                file=audio_file,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error("Failed to play audio", error=str(e))
            return False
    
    async def get_channel_variable(
        self,
        channel: str,
        variable: str
    ) -> Optional[str]:
        """
        Get channel variable value.
        
        Args:
            channel: Channel name
            variable: Variable name
        
        Returns:
            Variable value or None
        """
        if not self.connected:
            return None
        
        try:
            response = await self.ami.send_action({
                "Action": "GetVar",
                "Channel": channel,
                "Variable": variable
            })
            
            if response.get("Response") == "Success":
                return response.get("Value")
            
            return None
            
        except Exception as e:
            logger.error("Failed to get channel variable", error=str(e))
            return None
    
    async def set_channel_variable(
        self,
        channel: str,
        variable: str,
        value: str
    ) -> bool:
        """
        Set channel variable.
        
        Args:
            channel: Channel name
            variable: Variable name
            value: Variable value
        
        Returns:
            True if variable set successfully
        """
        if not self.connected:
            return False
        
        try:
            response = await self.ami.send_action({
                "Action": "SetVar",
                "Channel": channel,
                "Variable": variable,
                "Value": value
            })
            
            return response.get("Response") == "Success"
            
        except Exception as e:
            logger.error("Failed to set channel variable", error=str(e))
            return False
    
    def register_event_handler(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ):
        """
        Register custom event handler.
        
        Args:
            event_type: AMI event type
            handler: Async handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        
        logger.debug(
            "Event handler registered",
            event_type=event_type,
            handler=handler.__name__
        )
    
    async def execute_agi_command(
        self,
        channel: str,
        command: str,
        args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute AGI command on channel.
        
        Args:
            channel: Channel name
            command: AGI command
            args: Command arguments
        
        Returns:
            Command result
        """
        if not self.connected:
            raise RuntimeError("Not connected to Asterisk")
        
        command_line = command
        if args:
            command_line += " " + " ".join(args)
        
        try:
            response = await self.ami.send_action({
                "Action": "AGI",
                "Channel": channel,
                "Command": command_line
            })
            
            return {
                "success": response.get("Response") == "Success",
                "result": response.get("Result", ""),
                "data": response.get("ResultData", "")
            }
            
        except Exception as e:
            logger.error("Failed to execute AGI command", error=str(e))
            raise
    
    def get_active_calls(self) -> List[CallInfo]:
        """Get list of active calls."""
        return list(self.active_calls.values())
    
    def get_call_by_caller_id(self, caller_id: str) -> Optional[CallInfo]:
        """Get call info by caller ID."""
        for call in self.active_calls.values():
            if call.caller_id == caller_id:
                return call
        return None