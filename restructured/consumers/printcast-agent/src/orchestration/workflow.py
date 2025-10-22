"""
Main workflow orchestrator for PrintCast Agent.

Coordinates the entire voice-to-print-to-delivery workflow.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

import structlog
from pydantic import BaseModel, Field

from ..integrations.asterisk import AsteriskManager
from ..integrations.elevenlabs import ElevenLabsAgent
from ..integrations.content import ContentFetcher, ContentItem
from ..integrations.printing import PrintManager
from ..integrations.delivery import DeliveryService, Address

logger = structlog.get_logger(__name__)


class WorkflowState(Enum):
    """Workflow states."""
    IDLE = "idle"
    CALL_INITIATED = "call_initiated"
    GREETING = "greeting"
    CONTENT_SELECTION = "content_selection"
    USER_SELECTION = "user_selection"
    ADDRESS_COLLECTION = "address_collection"
    CONFIRMATION = "confirmation"
    PROCESSING = "processing"
    PRINTING = "printing"
    SHIPPING = "shipping"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowContext(BaseModel):
    """Context for workflow execution."""
    
    workflow_id: str
    session_id: str
    caller_id: str
    state: WorkflowState = WorkflowState.IDLE
    language: str = "cs"
    content_type: Optional[str] = None
    available_content: List[ContentItem] = Field(default_factory=list)
    selected_items: List[str] = Field(default_factory=list)
    delivery_address: Optional[Address] = None
    delivery_method: str = "post"
    print_job_ids: List[str] = Field(default_factory=list)
    shipment_id: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class WorkflowOrchestrator:
    """
    Orchestrates the complete voice-to-print workflow.
    
    Manages state transitions and coordinates all services.
    """
    
    def __init__(
        self,
        asterisk: AsteriskManager,
        elevenlabs: ElevenLabsAgent,
        content: ContentFetcher,
        printer: PrintManager,
        delivery: DeliveryService
    ):
        """
        Initialize workflow orchestrator.
        
        Args:
            asterisk: Asterisk manager
            elevenlabs: ElevenLabs agent
            content: Content fetcher
            printer: Print manager
            delivery: Delivery service
        """
        self.asterisk = asterisk
        self.elevenlabs = elevenlabs
        self.content = content
        self.printer = printer
        self.delivery = delivery
        
        self.workflows: Dict[str, WorkflowContext] = {}
        self.workflow_counter = 0
        
        logger.info("Workflow orchestrator initialized")
    
    async def start_workflow(
        self,
        caller_id: str,
        session_id: str,
        language: str = "cs"
    ) -> str:
        """
        Start a new workflow for incoming call.
        
        Args:
            caller_id: Caller phone number
            session_id: Call session ID
            language: Preferred language
        
        Returns:
            Workflow ID
        """
        try:
            # Create workflow context
            self.workflow_counter += 1
            workflow_id = f"wf_{self.workflow_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            context = WorkflowContext(
                workflow_id=workflow_id,
                session_id=session_id,
                caller_id=caller_id,
                language=language,
                state=WorkflowState.CALL_INITIATED
            )
            
            self.workflows[workflow_id] = context
            
            # Start workflow execution
            asyncio.create_task(self._execute_workflow(workflow_id))
            
            logger.info(
                "Workflow started",
                workflow_id=workflow_id,
                caller_id=caller_id,
                session_id=session_id
            )
            
            return workflow_id
            
        except Exception as e:
            logger.error("Failed to start workflow", error=str(e))
            raise
    
    async def _execute_workflow(self, workflow_id: str):
        """
        Execute the complete workflow.
        
        Args:
            workflow_id: Workflow ID
        """
        context = self.workflows.get(workflow_id)
        if not context:
            return
        
        try:
            # State machine execution
            while context.state not in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
                
                if context.state == WorkflowState.CALL_INITIATED:
                    await self._handle_call_initiated(context)
                    
                elif context.state == WorkflowState.GREETING:
                    await self._handle_greeting(context)
                    
                elif context.state == WorkflowState.CONTENT_SELECTION:
                    await self._handle_content_selection(context)
                    
                elif context.state == WorkflowState.USER_SELECTION:
                    await self._handle_user_selection(context)
                    
                elif context.state == WorkflowState.ADDRESS_COLLECTION:
                    await self._handle_address_collection(context)
                    
                elif context.state == WorkflowState.CONFIRMATION:
                    await self._handle_confirmation(context)
                    
                elif context.state == WorkflowState.PROCESSING:
                    await self._handle_processing(context)
                    
                elif context.state == WorkflowState.PRINTING:
                    await self._handle_printing(context)
                    
                elif context.state == WorkflowState.SHIPPING:
                    await self._handle_shipping(context)
                    
                else:
                    logger.warning(
                        "Unknown workflow state",
                        state=context.state,
                        workflow_id=workflow_id
                    )
                    context.state = WorkflowState.FAILED
                    
                # Small delay between state transitions
                await asyncio.sleep(0.1)
            
            # Workflow completed
            context.end_time = datetime.now()
            duration = (context.end_time - context.start_time).total_seconds()
            
            logger.info(
                "Workflow completed",
                workflow_id=workflow_id,
                state=context.state,
                duration=duration
            )
            
        except Exception as e:
            logger.error(
                "Workflow execution failed",
                workflow_id=workflow_id,
                error=str(e)
            )
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def _handle_call_initiated(self, context: WorkflowContext):
        """Handle call initiated state."""
        try:
            # Start ElevenLabs conversation
            await self.elevenlabs.start_conversation(
                session_id=context.session_id,
                language=context.language
            )
            
            context.state = WorkflowState.GREETING
            
        except Exception as e:
            logger.error("Failed to initiate call", error=str(e))
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def _handle_greeting(self, context: WorkflowContext):
        """Handle greeting state."""
        try:
            # Generate and play greeting
            greeting = self._get_greeting_text(context.language)
            
            response = await self.elevenlabs.text_to_speech(
                greeting,
                language=context.language
            )
            
            # Play audio through Asterisk
            # In production, would stream audio through SIP
            
            context.state = WorkflowState.CONTENT_SELECTION
            
        except Exception as e:
            logger.error("Failed to play greeting", error=str(e))
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def _handle_content_selection(self, context: WorkflowContext):
        """Handle content type selection."""
        try:
            # Ask user what content they want
            prompt = self._get_content_selection_prompt(context.language)
            
            await self.elevenlabs.send_message(
                context.session_id,
                prompt
            )
            
            # Wait for user response (simulated)
            await asyncio.sleep(2)
            
            # For demo, default to GitHub trending
            context.content_type = "github"
            
            # Fetch content
            context.available_content = await self.content.fetch_github_trending(
                limit=5
            )
            
            # Generate summary
            summary = await self.elevenlabs.generate_content_summary(
                [item.dict() for item in context.available_content],
                language=context.language,
                max_items=5
            )
            
            # Read summary to user
            await self.elevenlabs.send_message(
                context.session_id,
                summary
            )
            
            context.state = WorkflowState.USER_SELECTION
            
        except Exception as e:
            logger.error("Failed in content selection", error=str(e))
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def _handle_user_selection(self, context: WorkflowContext):
        """Handle user's content selection."""
        try:
            # Wait for user selection (simulated)
            # In production, would process DTMF or voice input
            await asyncio.sleep(3)
            
            # For demo, select first two items
            if len(context.available_content) >= 2:
                context.selected_items = [
                    context.available_content[0].id,
                    context.available_content[1].id
                ]
            else:
                context.selected_items = [item.id for item in context.available_content]
            
            # Confirm selection
            confirmation = self._get_selection_confirmation(
                context.selected_items,
                context.language
            )
            
            await self.elevenlabs.send_message(
                context.session_id,
                confirmation
            )
            
            context.state = WorkflowState.ADDRESS_COLLECTION
            
        except Exception as e:
            logger.error("Failed in user selection", error=str(e))
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def _handle_address_collection(self, context: WorkflowContext):
        """Handle delivery address collection."""
        try:
            # Ask for delivery address
            prompt = self._get_address_prompt(context.language)
            
            await self.elevenlabs.send_message(
                context.session_id,
                prompt
            )
            
            # For demo, use default address
            context.delivery_address = Address(
                name="Test Recipient",
                street="Václavské náměstí 1",
                city="Praha",
                postal_code="11000",
                country="CZ",
                phone=context.caller_id
            )
            
            # Confirm address
            address_confirmation = self._format_address_confirmation(
                context.delivery_address,
                context.language
            )
            
            await self.elevenlabs.send_message(
                context.session_id,
                address_confirmation
            )
            
            context.state = WorkflowState.CONFIRMATION
            
        except Exception as e:
            logger.error("Failed in address collection", error=str(e))
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def _handle_confirmation(self, context: WorkflowContext):
        """Handle order confirmation."""
        try:
            # Generate final confirmation
            summary = self._generate_order_summary(context)
            
            await self.elevenlabs.send_message(
                context.session_id,
                summary
            )
            
            # Wait for confirmation (simulated)
            await asyncio.sleep(2)
            
            # Assume confirmed
            context.state = WorkflowState.PROCESSING
            
            # Thank user
            thanks = self._get_thank_you_message(context.language)
            await self.elevenlabs.send_message(
                context.session_id,
                thanks
            )
            
        except Exception as e:
            logger.error("Failed in confirmation", error=str(e))
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def _handle_processing(self, context: WorkflowContext):
        """Handle order processing."""
        try:
            # Process the order
            result = await self.process_order(
                context.session_id,
                context.selected_items,
                context.delivery_address.dict() if context.delivery_address else {},
                context.delivery_method
            )
            
            context.print_job_ids = result.get("print_jobs", [])
            context.shipment_id = result.get("shipment_id")
            
            context.state = WorkflowState.PRINTING
            
        except Exception as e:
            logger.error("Failed in processing", error=str(e))
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def _handle_printing(self, context: WorkflowContext):
        """Handle printing state."""
        try:
            # Monitor print jobs
            all_completed = True
            
            for job_id in context.print_job_ids:
                status = self.printer.get_job_status(job_id)
                if status and status["status"] not in ["completed", "simulated"]:
                    all_completed = False
            
            if all_completed:
                context.state = WorkflowState.SHIPPING
            else:
                # Wait and check again
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error("Failed in printing", error=str(e))
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def _handle_shipping(self, context: WorkflowContext):
        """Handle shipping state."""
        try:
            if context.shipment_id:
                # Mark as shipped
                await self.delivery.ship_package(context.shipment_id)
            
            context.state = WorkflowState.COMPLETED
            
        except Exception as e:
            logger.error("Failed in shipping", error=str(e))
            context.state = WorkflowState.FAILED
            context.error = str(e)
    
    async def process_order(
        self,
        session_id: str,
        selected_items: List[str],
        delivery_address: Dict[str, Any],
        delivery_method: str = "post"
    ) -> Dict[str, Any]:
        """
        Process complete order from selection to shipping.
        
        Args:
            session_id: Session ID
            selected_items: Selected content IDs
            delivery_address: Delivery address
            delivery_method: Delivery method
        
        Returns:
            Order result with tracking information
        """
        try:
            # Get selected content
            content_items = await self.content.get_content_by_ids(selected_items)
            
            if not content_items:
                raise ValueError("No content items found")
            
            # Format content for printing
            formatted_content = self.content.format_for_print(
                content_items,
                format="markdown"
            )
            
            # Generate PDF
            pdf_path = await self.printer.generate_pdf(
                formatted_content,
                title=f"PrintCast Order {session_id}"
            )
            
            # Print document
            print_job_id = await self.printer.print_document(pdf_path)
            
            # Create shipment
            address = Address(**delivery_address) if isinstance(delivery_address, dict) else delivery_address
            
            shipment_id = await self.delivery.create_shipment(
                recipient=address,
                method=delivery_method,
                weight=100,  # Estimate
                metadata={
                    "session_id": session_id,
                    "content_count": len(content_items)
                }
            )
            
            # Get tracking info
            tracking_info = self.delivery.get_shipment_status(shipment_id)
            
            logger.info(
                "Order processed",
                session_id=session_id,
                print_job=print_job_id,
                shipment=shipment_id
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "print_jobs": [print_job_id],
                "shipment_id": shipment_id,
                "tracking_number": tracking_info.get("tracking_number") if tracking_info else None,
                "estimated_delivery": tracking_info.get("estimated_delivery") if tracking_info else None,
                "total_items": len(content_items)
            }
            
        except Exception as e:
            logger.error("Failed to process order", error=str(e))
            raise
    
    def _get_greeting_text(self, language: str) -> str:
        """Get greeting text."""
        greetings = {
            "cs": "Dobrý den! Vítejte v PrintCast. Mohu vám pomoci vytisknout a doručit nejnovější trendy z GitHubu, RSS kanálů nebo zpráv. Co by vás zajímalo?",
            "en": "Hello! Welcome to PrintCast. I can help you print and deliver the latest trends from GitHub, RSS feeds, or news. What would you like to explore?"
        }
        return greetings.get(language, greetings["en"])
    
    def _get_content_selection_prompt(self, language: str) -> str:
        """Get content selection prompt."""
        prompts = {
            "cs": "Řekněte 'GitHub' pro trendující repozitáře, 'RSS' pro nejnovější články, nebo 'zprávy' pro aktuální novinky.",
            "en": "Say 'GitHub' for trending repositories, 'RSS' for latest articles, or 'news' for current news."
        }
        return prompts.get(language, prompts["en"])
    
    def _get_selection_confirmation(self, items: List[str], language: str) -> str:
        """Get selection confirmation."""
        count = len(items)
        if language == "cs":
            return f"Vybrali jste {count} položek k tisku. Nyní potřebuji vaši doručovací adresu."
        else:
            return f"You've selected {count} items to print. Now I need your delivery address."
    
    def _get_address_prompt(self, language: str) -> str:
        """Get address prompt."""
        prompts = {
            "cs": "Prosím, řekněte mi vaši doručovací adresu včetně jména, ulice, města a PSČ.",
            "en": "Please tell me your delivery address including name, street, city, and postal code."
        }
        return prompts.get(language, prompts["en"])
    
    def _format_address_confirmation(self, address: Address, language: str) -> str:
        """Format address confirmation."""
        if language == "cs":
            return f"Doručovací adresa: {address.name}, {address.street}, {address.postal_code} {address.city}. Je to správně?"
        else:
            return f"Delivery address: {address.name}, {address.street}, {address.postal_code} {address.city}. Is this correct?"
    
    def _generate_order_summary(self, context: WorkflowContext) -> str:
        """Generate order summary."""
        items_count = len(context.selected_items)
        
        if context.language == "cs":
            return f"Shrnutí objednávky: {items_count} položek k tisku, doručení {context.delivery_method} na adresu {context.delivery_address.city if context.delivery_address else 'neznámá'}. Potvrzujete objednávku?"
        else:
            return f"Order summary: {items_count} items to print, {context.delivery_method} delivery to {context.delivery_address.city if context.delivery_address else 'unknown'}. Do you confirm the order?"
    
    def _get_thank_you_message(self, language: str) -> str:
        """Get thank you message."""
        messages = {
            "cs": "Děkuji za vaši objednávku! Vaše dokumenty budou vytištěny a odeslány. Obdržíte sledovací číslo SMS zprávou.",
            "en": "Thank you for your order! Your documents will be printed and shipped. You'll receive a tracking number via SMS."
        }
        return messages.get(language, messages["en"])
    
    async def cancel_workflow(self, workflow_id: str, reason: str = "user_request") -> bool:
        """
        Cancel a workflow.
        
        Args:
            workflow_id: Workflow ID
            reason: Cancellation reason
        
        Returns:
            True if cancelled successfully
        """
        context = self.workflows.get(workflow_id)
        if not context:
            return False
        
        if context.state in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
            return False
        
        try:
            # Cancel print jobs
            for job_id in context.print_job_ids:
                await self.printer.cancel_print_job(job_id)
            
            # Cancel shipment
            if context.shipment_id:
                await self.delivery.cancel_shipment(context.shipment_id)
            
            # End conversation
            await self.elevenlabs.end_conversation(context.session_id)
            
            context.state = WorkflowState.CANCELLED
            context.end_time = datetime.now()
            context.metadata["cancellation_reason"] = reason
            
            logger.info(
                "Workflow cancelled",
                workflow_id=workflow_id,
                reason=reason
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to cancel workflow",
                workflow_id=workflow_id,
                error=str(e)
            )
            return False
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status."""
        context = self.workflows.get(workflow_id)
        if not context:
            return None
        
        duration = None
        if context.end_time:
            duration = (context.end_time - context.start_time).total_seconds()
        elif context.state not in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
            duration = (datetime.now() - context.start_time).total_seconds()
        
        return {
            "workflow_id": workflow_id,
            "session_id": context.session_id,
            "caller_id": context.caller_id,
            "state": context.state.value,
            "language": context.language,
            "selected_items": len(context.selected_items),
            "print_jobs": context.print_job_ids,
            "shipment_id": context.shipment_id,
            "start_time": context.start_time.isoformat(),
            "end_time": context.end_time.isoformat() if context.end_time else None,
            "duration_seconds": duration,
            "error": context.error
        }