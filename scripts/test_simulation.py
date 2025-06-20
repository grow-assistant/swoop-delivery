#!/usr/bin/env python3
"""
Golf Course Delivery System - Test Simulation
Simulates orders and asset movements with dummy locations
"""
import asyncio
import random
import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import websockets
import threading

# Configuration
API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

# Golf course dummy locations (hole numbers)
GOLF_HOLES = list(range(1, 19))
CLUBHOUSE = "clubhouse"

# Sample orders items
MENU_ITEMS = [
    "Hot Dog", "Burger", "Beer", "Soda", "Water", "Chips", 
    "Candy Bar", "Golf Balls", "Tees", "Sandwich", "Energy Drink"
]

class GolfCourseSimulator:
    """Simulates a golf course delivery system"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.assets = []
        self.orders = []
        self.ws_client = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_api_health(self) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(f"{self.base_url}/")
            return response.status_code == 200
        except Exception as e:
            self.log(f"API health check failed: {e}", "ERROR")
            return False
    
    def get_assets(self) -> List[Dict[str, Any]]:
        """Get all delivery assets"""
        try:
            response = requests.get(f"{self.base_url}/api/assets")
            if response.status_code == 200:
                self.assets = response.json()
                return self.assets
            return []
        except Exception as e:
            self.log(f"Failed to get assets: {e}", "ERROR")
            return []
    
    def create_order(self, hole_number: int) -> Dict[str, Any]:
        """Create a new order at specified hole"""
        items = random.sample(MENU_ITEMS, k=random.randint(1, 3))
        order_data = {
            "hole_number": hole_number,
            "items": items,
            "special_instructions": f"Player at hole {hole_number} tee box"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/orders",
                json=order_data
            )
            if response.status_code == 200:
                order = response.json()
                self.orders.append(order)
                self.log(f"Created order {order['order_id']} for hole {hole_number} - Items: {', '.join(items)}")
                return order
        except Exception as e:
            self.log(f"Failed to create order: {e}", "ERROR")
        return {}
    
    def dispatch_order(self, order_id: str) -> Dict[str, Any]:
        """Dispatch an order to best available asset"""
        try:
            response = requests.post(
                f"{self.base_url}/api/orders/{order_id}/dispatch"
            )
            if response.status_code == 200:
                dispatch = response.json()
                self.log(
                    f"Order {order_id} dispatched to {dispatch['asset_name']} "
                    f"(ETA: {dispatch['eta_minutes']:.1f} min, "
                    f"Delivery at hole {dispatch['predicted_delivery_hole']})"
                )
                return dispatch
        except Exception as e:
            self.log(f"Failed to dispatch order {order_id}: {e}", "ERROR")
        return {}
    
    def update_asset_location(self, asset_id: str, location: Any):
        """Update asset location"""
        try:
            response = requests.post(
                f"{self.base_url}/api/assets/{asset_id}/location",
                json={"location": location}
            )
            if response.status_code == 200:
                self.log(f"Updated {asset_id} location to {location}")
                return response.json()
        except Exception as e:
            self.log(f"Failed to update asset location: {e}", "ERROR")
        return {}
    
    def complete_order(self, order_id: str):
        """Mark order as completed"""
        try:
            response = requests.post(
                f"{self.base_url}/api/orders/{order_id}/complete"
            )
            if response.status_code == 200:
                self.log(f"Order {order_id} completed")
                return response.json()
        except Exception as e:
            self.log(f"Failed to complete order: {e}", "ERROR")
        return {}
    
    async def simulate_asset_movement(self, asset: Dict[str, Any], duration: int = 60):
        """Simulate asset moving around the course"""
        asset_id = asset['asset_id']
        asset_type = asset['asset_type']
        
        # Determine movement pattern based on asset type
        if asset_type == "beverage_cart":
            # Carts follow their loop
            if asset.get('loop') == 'front_9':
                holes = list(range(1, 10))
            else:
                holes = list(range(10, 19))
        else:
            # Staff can go anywhere
            holes = GOLF_HOLES
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # Move to random hole in allowed range
            new_location = random.choice(holes)
            self.update_asset_location(asset_id, new_location)
            
            # Wait 10-20 seconds before next movement
            await asyncio.sleep(random.randint(10, 20))
    
    async def simulate_orders(self, num_orders: int = 10, interval: int = 30):
        """Simulate incoming orders"""
        for i in range(num_orders):
            # Random hole for order
            hole = random.choice(GOLF_HOLES)
            
            # Create order
            order = self.create_order(hole)
            if order:
                # Wait a bit then dispatch
                await asyncio.sleep(2)
                self.dispatch_order(order['order_id'])
            
            # Wait before next order
            await asyncio.sleep(interval)
    
    async def websocket_monitor(self):
        """Monitor WebSocket for real-time updates"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                self.log("Connected to WebSocket for real-time monitoring")
                async for message in websocket:
                    data = json.loads(message)
                    self.log(f"WebSocket Update: {data['type']} - {json.dumps(data, indent=2)}", "WS")
        except Exception as e:
            self.log(f"WebSocket error: {e}", "ERROR")
    
    async def run_simulation(self, duration: int = 300):
        """Run the complete simulation"""
        self.log("Starting Golf Course Delivery Simulation")
        
        # Check API health
        if not self.check_api_health():
            self.log("API is not healthy. Please ensure the service is running.", "ERROR")
            return
        
        # Get initial assets
        assets = self.get_assets()
        self.log(f"Found {len(assets)} delivery assets")
        
        # Create tasks for parallel execution
        tasks = []
        
        # Start WebSocket monitoring
        tasks.append(asyncio.create_task(self.websocket_monitor()))
        
        # Simulate asset movements
        for asset in assets[:3]:  # Limit to 3 assets for demo
            tasks.append(asyncio.create_task(
                self.simulate_asset_movement(asset, duration)
            ))
        
        # Simulate orders
        tasks.append(asyncio.create_task(
            self.simulate_orders(num_orders=10, interval=20)
        ))
        
        # Wait for simulation to complete
        await asyncio.sleep(duration)
        
        # Cancel remaining tasks
        for task in tasks:
            task.cancel()
        
        self.log("Simulation completed")
        
        # Print summary
        self.log("\n=== SIMULATION SUMMARY ===")
        self.log(f"Total orders created: {len(self.orders)}")
        self.log(f"Simulation duration: {duration} seconds")


async def main():
    """Main entry point"""
    simulator = GolfCourseSimulator()
    
    # Run simulation for 5 minutes
    await simulator.run_simulation(duration=300)


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════╗
    ║   Golf Course Delivery System Simulator    ║
    ║                                            ║
    ║   This will simulate:                      ║
    ║   - Random orders at different holes       ║
    ║   - Asset movements around the course      ║
    ║   - Order dispatching and completion       ║
    ║   - Real-time WebSocket updates           ║
    ╚════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())