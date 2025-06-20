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
    
    # 3. Create a new order
    print("\n--- New Order ---")
    order = Order(order_id="ORD123", hole_number=4)
    print(f"Incoming order for Hole {order.hole_number}.")

    # 4. Dispatch the order
    print("\nDispatching order...")
    dispatcher.dispatch_order(order)
    
    # 5. Show updated status
    print("\nUpdated Asset Status:")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")

if __name__ == "__main__":
    run_simulation() 