"""
Main simulation runner for the Swoop Delivery system.
"""
from .models import BeverageCart, DeliveryStaff, Order, OrderItem, AssetStatus
from .dispatcher import Dispatcher

def run_simulation():
    """Initializes assets and runs a sample dispatch scenario."""
    print("--- Swoop Delivery Simulation for Pinetree Country Club ---")
    print("--- Now powered by ML Prediction Service ---")
    
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
    
    # 3. Create orders with different characteristics
    print("\n--- Creating Orders ---")
    
    # Order 1: Simple order (just drinks)
    order1_items = [
        OrderItem(name="Bottled Water", quantity=2, complexity='simple', price=3.0),
        OrderItem(name="Gatorade", quantity=1, complexity='simple', price=4.0)
    ]
    order1 = Order(
        order_id="ORD123", 
        hole_number=4,
        items=order1_items,
        value=sum(item.price * item.quantity for item in order1_items),
        time_of_day='morning'
    )
    print(f"\nOrder 1: {len(order1.items)} items for Hole {order1.hole_number} (morning)")
    print(f"  Items: {', '.join(f'{item.quantity}x {item.name}' for item in order1.items)}")
    print(f"  Total value: ${order1.value:.2f}")

    # 4. Dispatch the first order
    print("\nDispatching order 1...")
    dispatcher.dispatch_order(order1)
    
    # 5. Create a more complex order
    order2_items = [
        OrderItem(name="Hot Dog", quantity=2, complexity='medium', price=8.0),
        OrderItem(name="Nachos", quantity=1, complexity='complex', price=12.0),
        OrderItem(name="Beer", quantity=4, complexity='simple', price=6.0)
    ]
    order2 = Order(
        order_id="ORD124",
        hole_number=15,
        items=order2_items,
        value=sum(item.price * item.quantity for item in order2_items),
        time_of_day='noon'
    )
    print(f"\nOrder 2: {len(order2.items)} items for Hole {order2.hole_number} (noon)")
    print(f"  Items: {', '.join(f'{item.quantity}x {item.name}' for item in order2.items)}")
    print(f"  Total value: ${order2.value:.2f}")
    
    # 6. Dispatch the second order
    print("\nDispatching order 2...")
    dispatcher.dispatch_order(order2)
    
    # 7. Show updated status
    print("\n--- Final Asset Status ---")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")
        if asset.current_orders:
            print(f"  Active orders: {', '.join(order.order_id for order in asset.current_orders)}")
    
    # 8. Show ML prediction confidence (optional)
    print("\n--- ML Model Confidence ---")
    ps = dispatcher.prediction_service
    for prediction_type in ['prep_time', 'travel_time', 'acceptance']:
        confidence = ps.get_prediction_confidence(prediction_type)
        print(f"{prediction_type}: {confidence['accuracy']:.1%} accuracy ({confidence['data_points']:,} training samples)")

if __name__ == "__main__":
    run_simulation() 