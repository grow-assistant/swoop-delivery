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
FRONT_NINE = list(range(1, 10))
BACK_NINE = list(range(10, 19))
CLUBHOUSE = "clubhouse"

# Sample orders items
MENU_ITEMS = [
    "Hot Dog", "Burger", "Beer", "Soda", "Water", "Chips", 
    "Candy Bar", "Golf Balls", "Tees", "Sandwich", "Energy Drink",
    "Gatorade", "Trail Mix", "Sunscreen", "Towel", "Ice Pack"
]

# Realistic time-based menu preferences
def get_menu_items_by_time():
    """Get menu items based on simulated time of day"""
    hour = datetime.now().hour
    
    if 6 <= hour < 10:  # Morning
        return ["Coffee", "Breakfast Sandwich", "Energy Bar", "Orange Juice", "Water"]
    elif 10 <= hour < 14:  # Midday
        return ["Beer", "Hot Dog", "Burger", "Soda", "Chips", "Water"]
    elif 14 <= hour < 17:  # Afternoon
        return ["Beer", "Energy Drink", "Snacks", "Ice Pack", "Water"]
    else:  # Evening
        return ["Beer", "Sandwich", "Chips", "Soda", "Water"]

class GolfCourseSimulator:
    """Simulates a golf course delivery system"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.assets = []
        self.orders = []
        self.ws_client = None
        self.asset_movement_patterns = {}
        
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
                # Initialize movement patterns for each asset
                for asset in self.assets:
                    self.asset_movement_patterns[asset['asset_id']] = {
                        'direction': random.choice(['forward', 'backward']),
                        'last_move_time': time.time(),
                        'idle_time': 0
                    }
                return self.assets
            return []
        except Exception as e:
            self.log(f"Failed to get assets: {e}", "ERROR")
            return []
    
    def create_order(self, hole_number: int) -> Dict[str, Any]:
        """Create a new order at specified hole"""
        # Use time-based menu or random items
        if random.random() < 0.7:  # 70% chance of time-based menu
            available_items = get_menu_items_by_time()
        else:
            available_items = MENU_ITEMS
        
        items = random.sample(available_items, k=random.randint(1, 3))
        
        # Add realistic special instructions
        special_instructions = random.choice([
            f"Player at hole {hole_number} tee box",
            f"Deliver to hole {hole_number} green",
            f"Group of {random.randint(2, 4)} at hole {hole_number}",
            f"Quick delivery needed at hole {hole_number}",
            f"Call when arriving at hole {hole_number}",
            ""  # No special instructions
        ])
        
        order_data = {
            "hole_number": hole_number,
            "items": items,
            "special_instructions": special_instructions
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
    
    def get_next_realistic_location(self, asset: Dict[str, Any], current_location: Any) -> Any:
        """Get next realistic location for an asset based on movement patterns"""
        asset_id = asset['asset_id']
        asset_type = asset['asset_type']
        pattern = self.asset_movement_patterns.get(asset_id, {})
        
        # Handle clubhouse location
        if current_location == "clubhouse":
            if asset_type == "beverage_cart":
                # Cart should go to first/last hole of their loop
                if asset.get('loop') == 'front_9':
                    return random.choice([1, 5])
                else:
                    return random.choice([10, 14])
            else:
                # Staff can go anywhere
                return random.choice(GOLF_HOLES)
        
        # Convert to int if needed
        try:
            current_hole = int(current_location)
        except:
            return random.choice(GOLF_HOLES)
        
        # Beverage cart movement
        if asset_type == "beverage_cart":
            if asset.get('loop') == 'front_9':
                valid_holes = FRONT_NINE
            else:
                valid_holes = BACK_NINE
            
            # Sequential movement with occasional jumps
            if random.random() < 0.8:  # 80% sequential movement
                if pattern.get('direction') == 'forward':
                    next_hole = current_hole + 1
                    if next_hole not in valid_holes:
                        pattern['direction'] = 'backward'
                        next_hole = current_hole - 1
                else:
                    next_hole = current_hole - 1
                    if next_hole not in valid_holes:
                        pattern['direction'] = 'forward'
                        next_hole = current_hole + 1
                return next_hole if next_hole in valid_holes else current_hole
            else:
                # Jump to service a different area
                return random.choice([h for h in valid_holes if abs(h - current_hole) > 2])
        
        # Delivery staff movement - more flexible
        else:
            # Staff tend to move between orders, can jump around more
            if random.random() < 0.3:  # 30% chance to return to clubhouse
                return "clubhouse"
            elif random.random() < 0.6:  # Move to nearby hole
                nearby_holes = [h for h in GOLF_HOLES if abs(h - current_hole) <= 3]
                return random.choice(nearby_holes) if nearby_holes else current_hole
            else:  # Jump to any hole
                return random.choice(GOLF_HOLES)
    
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
        """Simulate realistic asset movement around the course"""
        asset_id = asset['asset_id']
        asset_type = asset['asset_type']
        asset_name = asset['name']
        
        self.log(f"Starting movement simulation for {asset_name} ({asset_type})")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # Get current location from API
            try:
                response = requests.get(f"{self.base_url}/api/assets/{asset_id}")
                if response.status_code == 200:
                    current_asset = response.json()
                    current_location = current_asset['current_location']
                    
                    # Move based on asset status
                    if current_asset['status'] == 'available':
                        # Get realistic next location
                        new_location = self.get_next_realistic_location(current_asset, current_location)
                        
                        if new_location != current_location:
                            self.update_asset_location(asset_id, new_location)
                        
                        # Variable wait time based on movement
                        if new_location == "clubhouse":
                            wait_time = random.randint(20, 40)  # Longer wait at clubhouse
                        else:
                            wait_time = random.randint(10, 25)  # Normal movement time
                    else:
                        # Asset is busy, wait longer
                        wait_time = random.randint(30, 45)
                        
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                self.log(f"Error in movement simulation for {asset_name}: {e}", "ERROR")
                await asyncio.sleep(10)
    
    async def simulate_orders(self, num_orders: int = 10, interval: int = 30):
        """Simulate realistic incoming orders"""
        # Order patterns - busier during certain "hours"
        order_patterns = [
            {'holes': FRONT_NINE, 'weight': 0.6},  # Front nine gets more orders
            {'holes': BACK_NINE, 'weight': 0.4}
        ]
        
        for i in range(num_orders):
            # Weighted hole selection
            if random.random() < order_patterns[0]['weight']:
                hole = random.choice(order_patterns[0]['holes'])
            else:
                hole = random.choice(order_patterns[1]['holes'])
            
            # Occasionally cluster orders (groups playing together)
            if random.random() < 0.3 and i < num_orders - 1:  # 30% chance of clustered orders
                # Create 2-3 orders at nearby holes
                cluster_size = random.randint(2, 3)
                base_hole = hole
                
                for j in range(cluster_size):
                    cluster_hole = max(1, min(18, base_hole + random.randint(-1, 1)))
                    order = self.create_order(cluster_hole)
                    if order:
                        await asyncio.sleep(random.uniform(0.5, 2))
                        self.dispatch_order(order['order_id'])
                    
                    if j < cluster_size - 1:
                        await asyncio.sleep(random.randint(5, 10))
                
                i += cluster_size - 1
            else:
                # Single order
                order = self.create_order(hole)
                if order:
                    # Random delay before dispatch (simulating order preparation)
                    await asyncio.sleep(random.uniform(2, 5))
                    self.dispatch_order(order['order_id'])
            
            # Variable interval between order batches
            if i < num_orders - 1:
                # Rush hours have shorter intervals
                rush_hour = random.random() < 0.3
                if rush_hour:
                    wait_time = random.randint(10, 20)
                else:
                    wait_time = random.randint(interval - 10, interval + 10)
                
                await asyncio.sleep(wait_time)
    
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
        self.log("Starting Golf Course Delivery Simulation with Randomized Positions")
        
        # Check API health
        if not self.check_api_health():
            self.log("API is not healthy. Please ensure the service is running.", "ERROR")
            return
        
        # Get initial assets
        assets = self.get_assets()
        self.log(f"Found {len(assets)} delivery assets with randomized starting positions:")
        for asset in assets:
            self.log(f"  - {asset['name']} at location: {asset['current_location']}")
        
        # Create tasks for parallel execution
        tasks = []
        
        # Start WebSocket monitoring
        tasks.append(asyncio.create_task(self.websocket_monitor()))
        
        # Simulate asset movements (limit active movement simulations)
        moving_assets = random.sample(assets, min(4, len(assets)))  # Random selection of assets to move
        for asset in moving_assets:
            tasks.append(asyncio.create_task(
                self.simulate_asset_movement(asset, duration)
            ))
        
        # Simulate orders with variable rate
        total_orders = random.randint(8, 15)  # Random number of orders
        tasks.append(asyncio.create_task(
            self.simulate_orders(num_orders=total_orders, interval=25)
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
        self.log(f"Assets moved: {len(moving_assets)}")


async def main():
    """Main entry point"""
    simulator = GolfCourseSimulator()
    
    # Run simulation for 5 minutes (can be adjusted)
    await simulator.run_simulation(duration=300)


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════╗
    ║   Golf Course Delivery System Simulator    ║
    ║          with Randomized Positions         ║
    ║                                            ║
    ║   This will simulate:                      ║
    ║   - Random starting positions for assets   ║
    ║   - Realistic movement patterns            ║
    ║   - Time-based menu preferences           ║
    ║   - Order clustering (groups)              ║
    ║   - Variable demand patterns               ║
    ╚════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())