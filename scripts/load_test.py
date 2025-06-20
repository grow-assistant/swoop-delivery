#!/usr/bin/env python3
"""
Load Testing Script for Golf Course Delivery System
Simulates high volume of concurrent orders to test system performance
"""
import asyncio
import aiohttp
import time
import random
import statistics
from datetime import datetime
from typing import List, Dict, Any
import json
import argparse

# Configuration
API_BASE_URL = "http://localhost:8000"
GOLF_HOLES = list(range(1, 19))

# Test scenarios
SCENARIOS = {
    "normal": {
        "name": "Normal Load",
        "concurrent_users": 10,
        "orders_per_user": 5,
        "delay_between_orders": (5, 15),  # seconds
    },
    "peak": {
        "name": "Peak Hours",
        "concurrent_users": 50,
        "orders_per_user": 3,
        "delay_between_orders": (2, 8),
    },
    "stress": {
        "name": "Stress Test",
        "concurrent_users": 100,
        "orders_per_user": 2,
        "delay_between_orders": (1, 3),
    }
}

class LoadTester:
    """Load testing for Golf Course Delivery System"""
    
    def __init__(self, scenario: str = "normal"):
        self.scenario = SCENARIOS.get(scenario, SCENARIOS["normal"])
        self.metrics = {
            "orders_created": 0,
            "orders_dispatched": 0,
            "orders_failed": 0,
            "response_times": [],
            "errors": []
        }
        self.start_time = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    async def create_order(self, session: aiohttp.ClientSession, user_id: int) -> Dict[str, Any]:
        """Create a single order"""
        hole = random.choice(GOLF_HOLES)
        items = random.sample([
            "Beer", "Soda", "Water", "Hot Dog", "Burger", 
            "Chips", "Candy Bar", "Golf Balls"
        ], k=random.randint(1, 3))
        
        order_data = {
            "hole_number": hole,
            "items": items,
            "special_instructions": f"Test order from user {user_id}"
        }
        
        start = time.time()
        try:
            async with session.post(
                f"{API_BASE_URL}/api/orders",
                json=order_data
            ) as response:
                elapsed = time.time() - start
                self.metrics["response_times"].append(elapsed)
                
                if response.status == 200:
                    order = await response.json()
                    self.metrics["orders_created"] += 1
                    return {
                        "order_id": order["order_id"],
                        "created_at": time.time(),
                        "response_time": elapsed
                    }
                else:
                    self.metrics["orders_failed"] += 1
                    self.metrics["errors"].append(f"Order creation failed: {response.status}")
                    return None
                    
        except Exception as e:
            self.metrics["orders_failed"] += 1
            self.metrics["errors"].append(f"Order creation error: {str(e)}")
            return None
    
    async def dispatch_order(self, session: aiohttp.ClientSession, order_id: str) -> bool:
        """Dispatch an order"""
        start = time.time()
        try:
            async with session.post(
                f"{API_BASE_URL}/api/orders/{order_id}/dispatch"
            ) as response:
                elapsed = time.time() - start
                self.metrics["response_times"].append(elapsed)
                
                if response.status == 200:
                    self.metrics["orders_dispatched"] += 1
                    return True
                else:
                    self.metrics["errors"].append(f"Dispatch failed for {order_id}: {response.status}")
                    return False
                    
        except Exception as e:
            self.metrics["errors"].append(f"Dispatch error for {order_id}: {str(e)}")
            return False
    
    async def simulate_user(self, user_id: int):
        """Simulate a single user creating orders"""
        async with aiohttp.ClientSession() as session:
            orders_created = []
            
            for i in range(self.scenario["orders_per_user"]):
                # Create order
                order = await self.create_order(session, user_id)
                
                if order:
                    orders_created.append(order)
                    self.log(f"User {user_id} created order {order['order_id']}")
                    
                    # Wait a bit then dispatch
                    await asyncio.sleep(random.uniform(1, 3))
                    
                    # Dispatch the order
                    dispatched = await self.dispatch_order(session, order["order_id"])
                    if dispatched:
                        self.log(f"User {user_id} order {order['order_id']} dispatched")
                
                # Delay between orders
                if i < self.scenario["orders_per_user"] - 1:
                    delay = random.uniform(*self.scenario["delay_between_orders"])
                    await asyncio.sleep(delay)
            
            return orders_created
    
    async def run_load_test(self):
        """Run the load test"""
        self.log(f"Starting load test: {self.scenario['name']}")
        self.log(f"Concurrent users: {self.scenario['concurrent_users']}")
        self.log(f"Orders per user: {self.scenario['orders_per_user']}")
        
        self.start_time = time.time()
        
        # Create tasks for all users
        tasks = []
        for user_id in range(self.scenario["concurrent_users"]):
            task = asyncio.create_task(self.simulate_user(user_id))
            tasks.append(task)
        
        # Wait for all users to complete
        results = await asyncio.gather(*tasks)
        
        # Calculate metrics
        total_time = time.time() - self.start_time
        self.calculate_and_display_metrics(total_time)
    
    def calculate_and_display_metrics(self, total_time: float):
        """Calculate and display test metrics"""
        print("\n" + "="*60)
        print(f"LOAD TEST RESULTS - {self.scenario['name']}")
        print("="*60)
        
        # Basic metrics
        print(f"\nTest Duration: {total_time:.2f} seconds")
        print(f"Total Orders Created: {self.metrics['orders_created']}")
        print(f"Total Orders Dispatched: {self.metrics['orders_dispatched']}")
        print(f"Failed Operations: {self.metrics['orders_failed']}")
        
        # Response time statistics
        if self.metrics["response_times"]:
            avg_response = statistics.mean(self.metrics["response_times"])
            min_response = min(self.metrics["response_times"])
            max_response = max(self.metrics["response_times"])
            p95_response = statistics.quantiles(self.metrics["response_times"], n=20)[18]  # 95th percentile
            
            print(f"\nResponse Time Statistics:")
            print(f"  Average: {avg_response*1000:.2f} ms")
            print(f"  Min: {min_response*1000:.2f} ms")
            print(f"  Max: {max_response*1000:.2f} ms")
            print(f"  95th Percentile: {p95_response*1000:.2f} ms")
        
        # Throughput
        orders_per_second = self.metrics["orders_created"] / total_time
        print(f"\nThroughput: {orders_per_second:.2f} orders/second")
        
        # Success rate
        total_operations = self.metrics["orders_created"] + self.metrics["orders_failed"]
        if total_operations > 0:
            success_rate = (self.metrics["orders_created"] / total_operations) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        # Errors
        if self.metrics["errors"]:
            print(f"\nErrors encountered: {len(self.metrics['errors'])}")
            print("Sample errors:")
            for error in self.metrics["errors"][:5]:
                print(f"  - {error}")
        
        print("\n" + "="*60)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Load test the Golf Course Delivery System")
    parser.add_argument(
        "--scenario",
        choices=["normal", "peak", "stress"],
        default="normal",
        help="Load test scenario to run"
    )
    parser.add_argument(
        "--url",
        default=API_BASE_URL,
        help="Base URL of the API"
    )
    
    args = parser.parse_args()
    
    # Update base URL if provided
    global API_BASE_URL
    API_BASE_URL = args.url
    
    print(f"""
    ╔════════════════════════════════════════════╗
    ║   Golf Course Delivery Load Test           ║
    ║                                            ║
    ║   Scenario: {args.scenario.upper():10}             ║
    ║   Target: {API_BASE_URL:32} ║
    ╚════════════════════════════════════════════╝
    """)
    
    # Run the load test
    tester = LoadTester(args.scenario)
    await tester.run_load_test()


if __name__ == "__main__":
    asyncio.run(main())