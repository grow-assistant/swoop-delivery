"""
FastAPI application for Golf Course Delivery System
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional
import asyncio
import json
import logging
from datetime import datetime
import random

from ..models import Order, OrderStatus, AssetStatus, BeverageCart, DeliveryStaff
from ..dispatcher import Dispatcher
from .models import (
    OrderRequest, OrderResponse, AssetResponse, 
    DispatchResponse, AssetLocation, AssetStatusUpdate
)
from .database import get_db, init_db
from .websocket_manager import ConnectionManager
from prometheus_fastapi_instrumentator import Instrumentator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket manager for real-time updates
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Golf Course Delivery API...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Golf Course Delivery API...")

# Create FastAPI app
app = FastAPI(
    title="Golf Course Delivery System",
    description="API for managing on-course food and beverage deliveries",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# In-memory storage (will be replaced with database)
assets: List[AssetResponse] = []
orders: List[OrderResponse] = []
dispatcher: Optional[Dispatcher] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the system with default assets"""
    global assets, dispatcher
    
    # Define realistic starting locations
    front_nine_holes = list(range(1, 10))  # Holes 1-9
    back_nine_holes = list(range(10, 19))  # Holes 10-18
    all_locations = ["clubhouse"] + list(range(1, 19))  # All possible locations
    
    # Initialize assets with random realistic starting positions
    default_assets = [
        # Cart 1 - restricted to front 9, random starting hole
        BeverageCart(
            asset_id="cart1", 
            name="Reese", 
            loop="front_9", 
            current_location=random.choice(front_nine_holes)
        ),
        # Cart 2 - restricted to back 9, random starting hole
        BeverageCart(
            asset_id="cart2", 
            name="Bev-Cart 2", 
            loop="back_9", 
            current_location=random.choice(back_nine_holes)
        ),
        # Staff 1 - can be anywhere, higher chance of clubhouse
        DeliveryStaff(
            asset_id="staff1", 
            name="Esteban", 
            current_location=random.choice(["clubhouse", "clubhouse"] + list(range(1, 19)))
        ),
        # Staff 2 - can be anywhere
        DeliveryStaff(
            asset_id="staff2", 
            name="Dylan", 
            current_location=random.choice(all_locations)
        ),
        # Staff 3 - can be anywhere
        DeliveryStaff(
            asset_id="staff3", 
            name="Paige", 
            current_location=random.choice(all_locations)
        )
    ]
    
    assets = [AssetResponse.from_model(asset) for asset in default_assets]
    dispatcher = Dispatcher(default_assets)
    
    # Log initial positions
    logger.info("System initialized with randomized asset positions:")
    for asset in default_assets:
        logger.info(f"  - {asset.name} ({asset.asset_id}): Location {asset.current_location}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Golf Course Delivery System",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/assets", response_model=List[AssetResponse])
async def get_assets():
    """Get all delivery assets and their current status"""
    return assets

@app.get("/api/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str):
    """Get a specific asset by ID"""
    asset = next((a for a in assets if a.asset_id == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@app.post("/api/assets/{asset_id}/location", response_model=AssetResponse)
async def update_asset_location(asset_id: str, location: AssetLocation):
    """Update an asset's location"""
    asset = next((a for a in assets if a.asset_id == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset.current_location = location.location
    
    # Broadcast location update via WebSocket
    await manager.broadcast({
        "type": "location_update",
        "asset_id": asset_id,
        "location": location.location,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return asset

@app.post("/api/assets/{asset_id}/status", response_model=AssetResponse)
async def update_asset_status(asset_id: str, status_update: AssetStatusUpdate):
    """Update an asset's status"""
    asset = next((a for a in assets if a.asset_id == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset.status = status_update.status
    
    # Broadcast status update via WebSocket
    await manager.broadcast({
        "type": "status_update",
        "asset_id": asset_id,
        "status": status_update.status,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return asset

@app.get("/api/orders", response_model=List[OrderResponse])
async def get_orders():
    """Get all orders"""
    return orders

@app.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get a specific order by ID"""
    order = next((o for o in orders if o.order_id == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.post("/api/orders", response_model=OrderResponse)
async def create_order(order_request: OrderRequest):
    """Create a new order"""
    # Create order
    order = Order(
        order_id=f"ORD{len(orders) + 1:04d}",
        hole_number=order_request.hole_number
    )
    
    order_response = OrderResponse.from_model(order)
    orders.append(order_response)
    
    # Broadcast new order via WebSocket
    await manager.broadcast({
        "type": "new_order",
        "order": order_response.dict(),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.info(f"Created order {order.order_id} for hole {order.hole_number}")
    return order_response

@app.post("/api/orders/{order_id}/dispatch", response_model=DispatchResponse)
async def dispatch_order(order_id: str):
    """Dispatch an order to the best available asset"""
    global dispatcher
    
    # Find the order
    order_response = next((o for o in orders if o.order_id == order_id), None)
    if not order_response:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order_response.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order already dispatched")
    
    # Create Order model from response
    order = Order(
        order_id=order_response.order_id,
        hole_number=order_response.hole_number,
        status=order_response.status
    )
    
    # Dispatch the order
    assigned_asset = dispatcher.dispatch_order(order)
    
    if not assigned_asset:
        raise HTTPException(status_code=503, detail="No available assets")
    
    # Update order status
    order_response.status = OrderStatus.ASSIGNED
    order_response.assigned_to_id = assigned_asset.asset_id
    order_response.assigned_to_name = assigned_asset.name
    
    # Calculate ETA
    eta, predicted_hole = dispatcher.calculate_eta_and_destination(
        assigned_asset, 
        order.hole_number
    )
    
    dispatch_response = DispatchResponse(
        order_id=order_id,
        asset_id=assigned_asset.asset_id,
        asset_name=assigned_asset.name,
        eta_minutes=eta,
        predicted_delivery_hole=predicted_hole
    )
    
    # Update asset status
    asset_response = next(a for a in assets if a.asset_id == assigned_asset.asset_id)
    asset_response.status = AssetStatus.ON_DELIVERY
    asset_response.current_orders.append(order_id)
    
    # Broadcast dispatch via WebSocket
    await manager.broadcast({
        "type": "order_dispatched",
        "dispatch": dispatch_response.dict(),
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.info(f"Dispatched order {order_id} to {assigned_asset.name}")
    return dispatch_response

@app.post("/api/orders/{order_id}/complete", response_model=OrderResponse)
async def complete_order(order_id: str):
    """Mark an order as completed"""
    # Find the order
    order_response = next((o for o in orders if o.order_id == order_id), None)
    if not order_response:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order_response.status != OrderStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Order not in progress")
    
    # Update order status
    order_response.status = OrderStatus.DELIVERED
    
    # Update asset status
    if order_response.assigned_to_id:
        asset = next((a for a in assets if a.asset_id == order_response.assigned_to_id), None)
        if asset:
            asset.current_orders.remove(order_id)
            if not asset.current_orders:
                asset.status = AssetStatus.AVAILABLE
    
    # Broadcast completion via WebSocket
    await manager.broadcast({
        "type": "order_completed",
        "order_id": order_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    logger.info(f"Order {order_id} completed")
    return order_response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)