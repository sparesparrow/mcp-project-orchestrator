"""
Delivery service integration for PrintCast Agent.

Handles shipping and delivery through various carriers:
- Czech Post (Česká pošta)
- Zásilkovna
- DPD
- PPL
- Generic courier services
"""

import asyncio
import hashlib
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

import httpx
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class DeliveryMethod(Enum):
    """Supported delivery methods."""
    POST = "post"           # Czech Post
    ZASILKOVNA = "zasilkovna"  # Zásilkovna
    DPD = "dpd"
    PPL = "ppl"
    COURIER = "courier"     # Generic courier


class Address(BaseModel):
    """Delivery address."""
    
    name: str
    street: str
    city: str
    postal_code: str
    country: str = "CZ"
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None


class Shipment(BaseModel):
    """Shipment information."""
    
    shipment_id: str
    tracking_number: Optional[str] = None
    carrier: str
    status: str = "pending"
    recipient: Address
    sender: Optional[Address] = None
    weight_grams: int = 100
    dimensions_cm: Optional[Dict[str, float]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    price: Optional[float] = None
    currency: str = "CZK"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeliveryService:
    """
    Manages delivery and shipping operations.
    
    Integrates with multiple Czech and international carriers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize delivery service.
        
        Args:
            config: Configuration including:
                - carriers: Carrier-specific configurations
                - default_carrier: Default carrier to use
                - sender_address: Default sender address
                - api_keys: API keys for each carrier
        """
        self.config = config
        self.carriers = config.get("carriers", {})
        self.default_carrier = config.get("default_carrier", "post")
        self.sender_address = config.get("sender_address", {})
        self.api_keys = config.get("api_keys", {})
        
        self.client: Optional[httpx.AsyncClient] = None
        self.shipments: Dict[str, Shipment] = {}
        
        logger.info(
            "Delivery service initialized",
            carriers=list(self.carriers.keys()),
            default_carrier=self.default_carrier
        )
    
    async def initialize(self):
        """Initialize HTTP client and verify carrier APIs."""
        try:
            self.client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True
            )
            
            # Verify carrier APIs
            for carrier in self.carriers:
                if carrier in self.api_keys:
                    await self._verify_carrier_api(carrier)
                    
        except Exception as e:
            logger.error("Failed to initialize delivery service", error=str(e))
    
    async def shutdown(self):
        """Cleanup resources."""
        if self.client:
            await self.client.aclose()
        logger.info("Delivery service shutdown")
    
    def is_configured(self) -> bool:
        """Check if delivery service is configured."""
        return bool(self.carriers and self.sender_address)
    
    async def _verify_carrier_api(self, carrier: str) -> bool:
        """
        Verify carrier API is accessible.
        
        Args:
            carrier: Carrier name
        
        Returns:
            True if API is accessible
        """
        try:
            if carrier == "zasilkovna":
                # Verify Zásilkovna API
                api_key = self.api_keys.get("zasilkovna")
                if api_key:
                    response = await self.client.get(
                        "https://api.packeta.com/v1/branches",
                        params={"apiPassword": api_key, "limit": 1}
                    )
                    if response.status_code == 200:
                        logger.info("Zásilkovna API verified")
                        return True
                        
            elif carrier == "post":
                # Czech Post doesn't require API verification for basic services
                logger.info("Czech Post service available")
                return True
                
            # Add other carrier verifications as needed
            
        except Exception as e:
            logger.warning(
                "Failed to verify carrier API",
                carrier=carrier,
                error=str(e)
            )
        
        return False
    
    async def get_quote(
        self,
        address: str,
        method: str = "post",
        weight: int = 100,
        dimensions: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Get delivery quote.
        
        Args:
            address: Delivery address
            method: Delivery method
            weight: Package weight in grams
            dimensions: Package dimensions in cm
        
        Returns:
            Delivery quote with pricing and timing
        """
        try:
            # Parse address if string
            if isinstance(address, str):
                # Simple parsing - in production would use proper address parser
                parts = address.split(",")
                parsed_address = Address(
                    name="Recipient",
                    street=parts[0].strip() if len(parts) > 0 else "",
                    city=parts[1].strip() if len(parts) > 1 else "Praha",
                    postal_code=parts[2].strip() if len(parts) > 2 else "10000",
                    country="CZ"
                )
            else:
                parsed_address = address
            
            # Calculate price based on carrier and weight
            price = await self._calculate_price(method, weight, dimensions)
            
            # Estimate delivery time
            delivery_days = self._estimate_delivery_days(method)
            estimated_delivery = datetime.now() + timedelta(days=delivery_days)
            
            return {
                "price": price,
                "currency": "CZK",
                "estimated_delivery": estimated_delivery.isoformat(),
                "delivery_days": delivery_days,
                "carrier": method,
                "service_type": self._get_service_type(method, weight)
            }
            
        except Exception as e:
            logger.error("Failed to get delivery quote", error=str(e))
            raise
    
    async def _calculate_price(
        self,
        method: str,
        weight: int,
        dimensions: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate delivery price."""
        # Simplified pricing - in production would use carrier APIs
        base_prices = {
            "post": 89.0,      # Czech Post standard letter
            "zasilkovna": 65.0,  # Zásilkovna to pickup point
            "dpd": 120.0,      # DPD standard
            "ppl": 115.0,      # PPL standard
            "courier": 150.0   # Generic courier
        }
        
        price = base_prices.get(method, 100.0)
        
        # Add weight surcharge
        if weight > 1000:  # Over 1kg
            price += (weight // 1000) * 20
        elif weight > 500:  # Over 500g
            price += 15
        
        # Add dimension surcharge for large packages
        if dimensions:
            volume = dimensions.get("length", 0) * dimensions.get("width", 0) * dimensions.get("height", 0)
            if volume > 50000:  # Over 50x50x20 cm
                price += 30
        
        return price
    
    def _estimate_delivery_days(self, method: str) -> int:
        """Estimate delivery time in days."""
        estimates = {
            "post": 2,        # Czech Post D+2
            "zasilkovna": 1,  # Next day to pickup point
            "dpd": 1,         # Next day delivery
            "ppl": 1,         # Next day delivery
            "courier": 0      # Same day possible
        }
        return estimates.get(method, 3)
    
    def _get_service_type(self, method: str, weight: int) -> str:
        """Determine service type based on method and weight."""
        if method == "post":
            if weight <= 50:
                return "Obyčejné psaní"
            elif weight <= 500:
                return "Doporučené psaní"
            else:
                return "Balík Do ruky"
        elif method == "zasilkovna":
            return "Na výdejní místo"
        else:
            return "Standard delivery"
    
    async def create_shipment(
        self,
        recipient: Address,
        method: str = "post",
        weight: int = 100,
        dimensions: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new shipment.
        
        Args:
            recipient: Recipient address
            method: Delivery method
            weight: Package weight in grams
            dimensions: Package dimensions
            metadata: Additional metadata
        
        Returns:
            Shipment ID
        """
        try:
            # Generate shipment ID
            shipment_id = f"ship_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(recipient.name.encode()).hexdigest()[:8]}"
            
            # Create shipment record
            shipment = Shipment(
                shipment_id=shipment_id,
                carrier=method,
                recipient=recipient,
                sender=Address(**self.sender_address) if self.sender_address else None,
                weight_grams=weight,
                dimensions_cm=dimensions,
                metadata=metadata or {}
            )
            
            # Calculate price
            shipment.price = await self._calculate_price(method, weight, dimensions)
            
            # Create shipment with carrier
            tracking_number = await self._create_carrier_shipment(shipment)
            if tracking_number:
                shipment.tracking_number = tracking_number
                shipment.status = "created"
            
            self.shipments[shipment_id] = shipment
            
            logger.info(
                "Shipment created",
                shipment_id=shipment_id,
                carrier=method,
                tracking=tracking_number
            )
            
            return shipment_id
            
        except Exception as e:
            logger.error("Failed to create shipment", error=str(e))
            raise
    
    async def _create_carrier_shipment(self, shipment: Shipment) -> Optional[str]:
        """
        Create shipment with specific carrier.
        
        Args:
            shipment: Shipment details
        
        Returns:
            Tracking number if available
        """
        try:
            if shipment.carrier == "zasilkovna":
                return await self._create_zasilkovna_shipment(shipment)
            elif shipment.carrier == "post":
                return await self._create_post_shipment(shipment)
            else:
                # Simulated tracking number for other carriers
                return f"{shipment.carrier.upper()}{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
        except Exception as e:
            logger.error(
                "Failed to create carrier shipment",
                carrier=shipment.carrier,
                error=str(e)
            )
            return None
    
    async def _create_zasilkovna_shipment(self, shipment: Shipment) -> Optional[str]:
        """Create shipment with Zásilkovna."""
        api_key = self.api_keys.get("zasilkovna")
        if not api_key:
            logger.warning("Zásilkovna API key not configured")
            return None
        
        try:
            # Prepare packet data
            packet_data = {
                "apiPassword": api_key,
                "packet": {
                    "number": shipment.shipment_id,
                    "name": shipment.recipient.name,
                    "surname": "",  # Would need to parse from name
                    "email": shipment.recipient.email or "",
                    "phone": shipment.recipient.phone or "",
                    "addressId": 1,  # Would need to select pickup point
                    "currency": shipment.currency,
                    "value": shipment.price,
                    "weight": shipment.weight_grams / 1000,  # Convert to kg
                    "eshop": "PrintCast"
                }
            }
            
            response = await self.client.post(
                "https://api.packeta.com/v1/packets",
                json=packet_data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("barcode")
            else:
                logger.error(
                    "Zásilkovna API error",
                    status=response.status_code,
                    response=response.text
                )
                return None
                
        except Exception as e:
            logger.error("Failed to create Zásilkovna shipment", error=str(e))
            return None
    
    async def _create_post_shipment(self, shipment: Shipment) -> Optional[str]:
        """Create shipment with Czech Post."""
        # Czech Post integration would require their B2B API
        # For now, return simulated tracking number
        tracking = f"RR{datetime.now().strftime('%Y%m%d%H%M')}CZ"
        
        logger.info(
            "Czech Post shipment simulated",
            tracking=tracking,
            recipient=shipment.recipient.city
        )
        
        return tracking
    
    async def ship_package(
        self,
        shipment_id: str,
        pickup_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Mark package as shipped and arrange pickup.
        
        Args:
            shipment_id: Shipment ID
            pickup_time: Optional pickup time
        
        Returns:
            Shipping confirmation
        """
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            raise ValueError(f"Shipment {shipment_id} not found")
        
        try:
            # Update shipment status
            shipment.status = "shipped"
            shipment.shipped_at = datetime.now()
            
            # Arrange pickup if needed
            pickup_confirmation = None
            if pickup_time:
                pickup_confirmation = await self._arrange_pickup(
                    shipment,
                    pickup_time
                )
            
            logger.info(
                "Package shipped",
                shipment_id=shipment_id,
                tracking=shipment.tracking_number
            )
            
            return {
                "shipment_id": shipment_id,
                "tracking_number": shipment.tracking_number,
                "carrier": shipment.carrier,
                "status": "shipped",
                "pickup_confirmation": pickup_confirmation,
                "estimated_delivery": (
                    shipment.shipped_at + timedelta(days=self._estimate_delivery_days(shipment.carrier))
                ).isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to ship package", error=str(e))
            raise
    
    async def _arrange_pickup(
        self,
        shipment: Shipment,
        pickup_time: datetime
    ) -> Optional[str]:
        """Arrange carrier pickup."""
        # In production, would call carrier pickup APIs
        confirmation = f"PICKUP-{shipment.carrier.upper()}-{pickup_time.strftime('%Y%m%d')}"
        
        logger.info(
            "Pickup arranged",
            carrier=shipment.carrier,
            time=pickup_time.isoformat(),
            confirmation=confirmation
        )
        
        return confirmation
    
    async def track_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """
        Track shipment status.
        
        Args:
            shipment_id: Shipment ID
        
        Returns:
            Tracking information
        """
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            raise ValueError(f"Shipment {shipment_id} not found")
        
        try:
            # Get tracking from carrier
            tracking_info = await self._get_carrier_tracking(shipment)
            
            # Update local status if changed
            if tracking_info.get("delivered"):
                shipment.status = "delivered"
                shipment.delivered_at = datetime.now()
            elif tracking_info.get("in_transit"):
                shipment.status = "in_transit"
            
            return {
                "shipment_id": shipment_id,
                "tracking_number": shipment.tracking_number,
                "status": shipment.status,
                "carrier": shipment.carrier,
                "shipped_at": shipment.shipped_at.isoformat() if shipment.shipped_at else None,
                "delivered_at": shipment.delivered_at.isoformat() if shipment.delivered_at else None,
                "tracking_events": tracking_info.get("events", [])
            }
            
        except Exception as e:
            logger.error("Failed to track shipment", error=str(e))
            raise
    
    async def _get_carrier_tracking(self, shipment: Shipment) -> Dict[str, Any]:
        """Get tracking info from carrier."""
        # In production, would call carrier tracking APIs
        # For now, return simulated tracking
        
        events = []
        if shipment.shipped_at:
            events.append({
                "timestamp": shipment.shipped_at.isoformat(),
                "status": "Picked up",
                "location": "Praha"
            })
            
            if shipment.status == "in_transit":
                events.append({
                    "timestamp": (shipment.shipped_at + timedelta(hours=4)).isoformat(),
                    "status": "In transit",
                    "location": "Distribution center"
                })
            
            if shipment.status == "delivered":
                events.append({
                    "timestamp": shipment.delivered_at.isoformat(),
                    "status": "Delivered",
                    "location": shipment.recipient.city
                })
        
        return {
            "events": events,
            "in_transit": shipment.status == "in_transit",
            "delivered": shipment.status == "delivered"
        }
    
    async def cancel_shipment(self, shipment_id: str) -> bool:
        """
        Cancel a shipment.
        
        Args:
            shipment_id: Shipment ID
        
        Returns:
            True if cancelled successfully
        """
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            return False
        
        if shipment.status in ["delivered", "cancelled"]:
            return False
        
        try:
            # Cancel with carrier
            if shipment.tracking_number:
                await self._cancel_carrier_shipment(shipment)
            
            shipment.status = "cancelled"
            
            logger.info(
                "Shipment cancelled",
                shipment_id=shipment_id
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to cancel shipment",
                shipment_id=shipment_id,
                error=str(e)
            )
            return False
    
    async def _cancel_carrier_shipment(self, shipment: Shipment):
        """Cancel shipment with carrier."""
        # In production, would call carrier cancellation APIs
        logger.info(
            "Carrier shipment cancellation simulated",
            carrier=shipment.carrier,
            tracking=shipment.tracking_number
        )
    
    def get_shipment_status(self, shipment_id: str) -> Optional[Dict[str, Any]]:
        """Get shipment status."""
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            return None
        
        return {
            "shipment_id": shipment.shipment_id,
            "status": shipment.status,
            "tracking_number": shipment.tracking_number,
            "carrier": shipment.carrier,
            "recipient": {
                "name": shipment.recipient.name,
                "city": shipment.recipient.city,
                "country": shipment.recipient.country
            },
            "price": shipment.price,
            "currency": shipment.currency,
            "created": shipment.created_at.isoformat(),
            "shipped": shipment.shipped_at.isoformat() if shipment.shipped_at else None,
            "delivered": shipment.delivered_at.isoformat() if shipment.delivered_at else None
        }
    
    async def generate_shipping_label(
        self,
        shipment_id: str,
        format: str = "pdf"
    ) -> bytes:
        """
        Generate shipping label.
        
        Args:
            shipment_id: Shipment ID
            format: Label format (pdf, zpl, png)
        
        Returns:
            Label data
        """
        shipment = self.shipments.get(shipment_id)
        if not shipment:
            raise ValueError(f"Shipment {shipment_id} not found")
        
        # In production, would generate actual label
        # For now, return placeholder
        label_content = f"""
        SHIPPING LABEL
        ===============
        From: {shipment.sender.name if shipment.sender else 'PrintCast'}
        To: {shipment.recipient.name}
            {shipment.recipient.street}
            {shipment.recipient.postal_code} {shipment.recipient.city}
            {shipment.recipient.country}
        
        Tracking: {shipment.tracking_number or 'N/A'}
        Carrier: {shipment.carrier.upper()}
        Weight: {shipment.weight_grams}g
        """
        
        return label_content.encode("utf-8")