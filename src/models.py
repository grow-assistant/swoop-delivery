"""
Data models for the delivery system.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional

class AssetStatus(Enum):
    """Represents the status of a delivery asset."""
    AVAILABLE = "available"
    ON_DELIVERY = "on_delivery"
    INACTIVE = "inactive"

class OrderStatus(Enum):
    """Represents the status of an order."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class DeliveryAsset:
    """Base class for a delivery asset. Not a dataclass itself."""
    pass

@dataclass
class BeverageCart(DeliveryAsset):
    """Represents a beverage cart that is restricted to a specific loop."""
    asset_id: str
    name: str
    loop: str  # "front_9" or "back_9"
    status: AssetStatus = AssetStatus.AVAILABLE
    current_location: any = "clubhouse"
    current_orders: list = field(default_factory=list)

@dataclass
class DeliveryStaff(DeliveryAsset):
    """Represents a delivery staff member who can roam the entire course."""
    asset_id: str
    name: str
    status: AssetStatus = AssetStatus.AVAILABLE
    current_location: any = "clubhouse"
    current_orders: list = field(default_factory=list)

@dataclass
class OrderItem:
    """Represents an item in an order."""
    name: str
    quantity: int = 1
    complexity: str = 'medium'  # 'simple', 'medium', or 'complex'
    price: float = 0.0

@dataclass
class Order:
    """Represents a customer order."""
    order_id: str
    hole_number: int
    status: OrderStatus = OrderStatus.PENDING
    assigned_to: DeliveryAsset = None
    items: List[OrderItem] = field(default_factory=list)
    value: float = 0.0
    time_of_day: Optional[str] = None  # 'morning', 'noon', 'afternoon' 