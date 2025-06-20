"""
Main simulation runner for the Swoop Delivery system.
"""
from .models import BeverageCart, DeliveryStaff, Order, AssetStatus
from .dispatcher import Dispatcher

def run_simulation():
    """Initializes assets and runs a sample dispatch scenario."""
    print("--- Swoop Delivery Simulation for Pinetree Country Club ---")
    
    # 1. Initialize Delivery Assets
    assets = [
        BeverageCart(asset_id="cart1", name="Reese", loop="front_9", current_location=2),
        BeverageCart(asset_id="cart2", name="Bev-Cart 2", loop="back_9", current_location="clubhouse"),
        DeliveryStaff(asset_id="staff1", name="Esteban", current_location="clubhouse"),
        DeliveryStaff(asset_id="staff2", name="Dylan", current_location=18),
        DeliveryStaff(asset_id="staff3", name="Paige", status=AssetStatus.ON_DELIVERY)
    ]
    
    print("\nInitial Asset Status:")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")
        
    # 2. Initialize Dispatcher
    dispatcher = Dispatcher(assets)
    
    # 3. Test single order dispatch
    print("\n--- Test 1: Single Order Dispatch ---")
    order1 = Order(order_id="ORD123", hole_number=4)
    print(f"Incoming order for Hole {order1.hole_number}.")
    dispatcher.dispatch_order(order1, consider_batching=False)
    
    # Reset assets for next test
    for asset in assets:
        if asset.name in ["Reese", "Esteban"]:  # Reset the assets that might have been used
            asset.status = AssetStatus.AVAILABLE
            asset.current_orders = []
    
    # 4. Test batch order dispatch
    print("\n\n--- Test 2: Batch Order Dispatch ---")
    print("Creating multiple orders that can be batched:")
    
    # Create orders at adjacent holes
    order2 = Order(order_id="ORD124", hole_number=5)
    order3 = Order(order_id="ORD125", hole_number=6)
    order4 = Order(order_id="ORD126", hole_number=7)
    
    # Add orders to pending list
    dispatcher.add_pending_order(order2)
    dispatcher.add_pending_order(order3)
    dispatcher.add_pending_order(order4)
    
    print(f"\nIncoming orders: Holes {order2.hole_number}, {order3.hole_number}, {order4.hole_number}")
    print("\nDispatching with batching enabled...")
    dispatcher.dispatch_order(order2, consider_batching=True)
    
    # 5. Show final status
    print("\n\n--- Final Asset Status ---")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")
        if asset.current_orders:
            order_ids = [o.order_id for o in asset.current_orders]
            print(f"  → Current orders: {order_ids}")

if __name__ == "__main__":
    run_simulation() 