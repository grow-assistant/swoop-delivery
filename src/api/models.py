"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime
from ..models import AssetStatus, OrderStatus, BeverageCart, DeliveryStaff, Order

class OrderRequest(BaseModel):
    """Request model for creating a new order"""
    hole_number: int = Field(..., ge=1, le=18, description="Hole number where the order is placed")
    items: Optional[List[str]] = Field(default=[], description="List of items ordered")
    special_instructions: Optional[str] = None

class AssetLocation(BaseModel):
    """Request model for updating asset location"""
    location: Union[int, str] = Field(..., description="Current location (hole number or 'clubhouse')")

class AssetStatusUpdate(BaseModel):
    """Request model for updating asset status"""
    status: AssetStatus

class AssetResponse(BaseModel):
    """Response model for delivery assets"""
    asset_id: str
    name: str
    asset_type: str  # "beverage_cart" or "delivery_staff"
    status: AssetStatus
    current_location: Union[int, str]
    current_orders: List[str] = []
    loop: Optional[str] = None  # Only for beverage carts

    @classmethod
    def from_model(cls, asset: Union[BeverageCart, DeliveryStaff]) -> 'AssetResponse':
        """Create response from domain model"""
        asset_type = "beverage_cart" if isinstance(asset, BeverageCart) else "delivery_staff"
        return cls(
            asset_id=asset.asset_id,
            name=asset.name,
            asset_type=asset_type,
            status=asset.status,
            current_location=asset.current_location,
            current_orders=[o.order_id for o in asset.current_orders],
            loop=getattr(asset, 'loop', None)
        )

class OrderResponse(BaseModel):
    """Response model for orders"""
    order_id: str
    hole_number: int
    status: OrderStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    completed_at: Optional[datetime] = None

    @classmethod
    def from_model(cls, order: Order) -> 'OrderResponse':
        """Create response from domain model"""
        return cls(
            order_id=order.order_id,
            hole_number=order.hole_number,
            status=order.status,
            assigned_to_id=getattr(order.assigned_to, 'asset_id', None),
            assigned_to_name=getattr(order.assigned_to, 'name', None)
        )

class DispatchResponse(BaseModel):
    """Response model for dispatch operation"""
    order_id: str
    asset_id: str
    asset_name: str
    eta_minutes: float
    predicted_delivery_hole: int

class SystemMetrics(BaseModel):
    """Response model for system metrics"""
    total_orders: int
    pending_orders: int
    active_deliveries: int
    completed_deliveries: int
    available_assets: int
    busy_assets: int
    average_delivery_time: Optional[float] = None

class Config:
    """Pydantic config"""
    orm_mode = True
    use_enum_values = True