"""
Demo of the refined asset movement simulation with state-driven behavior.
"""
from .models import BeverageCart, DeliveryStaff, Order, AssetStatus
from .dispatcher import Dispatcher
from .simulation import AssetSimulator
import time


def run_movement_simulation():
    """Demonstrates the state-driven asset movement simulation."""
    print("=== State-Driven Asset Movement Simulation ===\n")
    
    # Initialize assets
    assets = [
        BeverageCart(asset_id="cart1", name="Front Cart", loop="front_9", current_location=2),
        BeverageCart(asset_id="cart2", name="Back Cart", loop="back_9", current_location=15),
        DeliveryStaff(asset_id="staff1", name="Alice", current_location=5),
        DeliveryStaff(asset_id="staff2", name="Bob", current_location="clubhouse"),
    ]
    
    # Initialize dispatcher and simulator
    dispatcher = Dispatcher(assets)
    simulator = AssetSimulator()
    
    print("Initial Asset States:")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")
    
    # Simulate several time steps
    print("\n--- Starting Simulation ---\n")
    
    # Time step 1: IDLE assets may reposition
    print("Time Step 1: IDLE Asset Movement")
    for asset in assets:
        simulator.simulate_asset_movement(asset)
    print()
    
    # Create and dispatch an order
    print("Time Step 2: New Order Arrives")
    order1 = Order(order_id="ORD001", hole_number=7)
    print(f"New order for Hole {order1.hole_number}")
    dispatcher.dispatch_order(order1)
    print()
    
    # Time step 3: Assets move based on their states
    print("Time Step 3: State-Based Movement")
    for asset in assets:
        print(f"\nMoving {asset.name} (Status: {asset.status.value}):")
        simulator.simulate_asset_movement(asset)
    
    # Time step 4: Continue movement
    print("\nTime Step 4: Continued Movement")
    for asset in assets:
        simulator.simulate_asset_movement(asset)
    print()
    
    # Create another order
    print("Time Step 5: Another Order Arrives")
    order2 = Order(order_id="ORD002", hole_number=12)
    print(f"New order for Hole {order2.hole_number}")
    dispatcher.dispatch_order(order2)
    print()
    
    # Simulate delivery completion over multiple steps
    for step in range(6, 12):
        print(f"\nTime Step {step}: Asset Movement")
        for asset in assets:
            old_status = asset.status
            simulator.simulate_asset_movement(asset)
            if old_status != asset.status:
                print(f"  {asset.name} status changed: {old_status.value} -> {asset.status.value}")
        
    # Final status
    print("\n--- Final Asset States ---")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")
        if asset.current_orders:
            print(f"  Current orders: {[o.order_id for o in asset.current_orders]}")


def demonstrate_state_transitions():
    """Demonstrates all possible state transitions for an asset."""
    print("\n=== State Transition Demonstration ===\n")
    
    # Create a test asset
    test_asset = DeliveryStaff(asset_id="test", name="Test Staff", current_location=5)
    simulator = AssetSimulator()
    
    print(f"Initial state: {test_asset.status.value} at location {test_asset.current_location}")
    
    # 1. IDLE -> EN_ROUTE_TO_PICKUP
    print("\n1. Assigning order (IDLE -> EN_ROUTE_TO_PICKUP)")
    order = Order(order_id="TEST001", hole_number=10)
    simulator.update_asset_state_for_new_order(test_asset, order)
    
    # 2. EN_ROUTE_TO_PICKUP -> WAITING_FOR_ORDER
    print("\n2. Moving to clubhouse")
    while test_asset.status == AssetStatus.EN_ROUTE_TO_PICKUP:
        simulator.simulate_asset_movement(test_asset)
    
    # 3. WAITING_FOR_ORDER -> EN_ROUTE_TO_DROPOFF
    print("\n3. Waiting for order to be ready")
    while test_asset.status == AssetStatus.WAITING_FOR_ORDER:
        simulator.simulate_asset_movement(test_asset)
    
    # 4. EN_ROUTE_TO_DROPOFF -> IDLE
    print("\n4. Delivering order")
    while test_asset.status == AssetStatus.EN_ROUTE_TO_DROPOFF:
        simulator.simulate_asset_movement(test_asset)
    
    print(f"\nFinal state: {test_asset.status.value} at location {test_asset.current_location}")


def compare_movement_patterns():
    """Compare movement patterns between different asset types."""
    print("\n=== Movement Pattern Comparison ===\n")
    
    cart = BeverageCart(asset_id="cart", name="Test Cart", loop="front_9", current_location=5)
    staff = DeliveryStaff(asset_id="staff", name="Test Staff", current_location=5)
    simulator = AssetSimulator()
    
    print("Testing IDLE repositioning behavior:")
    print(f"Cart starting at hole {cart.current_location} (restricted to front 9)")
    print(f"Staff starting at hole {staff.current_location} (no restrictions)")
    
    # Simulate 10 repositioning attempts
    cart_locations = []
    staff_locations = []
    
    for _ in range(10):
        # Force repositioning by directly calling get_next_realistic_location
        cart_new = simulator.get_next_realistic_location(cart)
        staff_new = simulator.get_next_realistic_location(staff)
        
        cart_locations.append(cart_new)
        staff_locations.append(staff_new)
        
        cart.current_location = cart_new
        staff.current_location = staff_new
    
    print(f"\nCart visited locations: {cart_locations}")
    print(f"Staff visited locations: {staff_locations}")
    
    # Verify cart stayed in its loop
    cart_valid = all(1 <= loc <= 9 for loc in cart_locations if isinstance(loc, int))
    print(f"\nCart stayed in front 9: {cart_valid}")
    
    # Check staff mobility
    staff_range = [loc for loc in staff_locations if isinstance(loc, int)]
    if staff_range:
        print(f"Staff location range: {min(staff_range)} to {max(staff_range)}")


if __name__ == "__main__":
    # Run the main simulation
    run_movement_simulation()
    
    # Demonstrate state transitions
    demonstrate_state_transitions()
    
    # Compare movement patterns
    compare_movement_patterns()