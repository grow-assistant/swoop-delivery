"""
Main simulation runner for the Swoop Delivery system.
"""
from .models import BeverageCart, DeliveryStaff, Order, OrderItem, AssetStatus
from .dispatcher import Dispatcher

def run_simulation():
    """Initializes assets and runs a sample dispatch scenario."""
    print("--- Swoop Delivery Simulation for Pinetree Country Club ---")
    print("--- Now powered by ML Prediction Service with Batch Order Support ---")
    
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
    
    # 3. Test single order dispatch with ML predictions
    print("\n--- Test 1: Single Order Dispatch with ML Predictions ---")
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
    
    print("\nDispatching order 1...")
    dispatcher.dispatch_order(order1, consider_batching=False)
    
    # Reset assets for next test
    for asset in assets:
        if asset.name in ["Reese", "Esteban"]:  # Reset the assets that might have been used
            asset.status = AssetStatus.AVAILABLE
            asset.current_orders = []
    
    # 4. Test batch order dispatch with ML predictions
    print("\n\n--- Test 2: Batch Order Dispatch with ML Predictions ---")
    print("Creating multiple orders that can be batched:")
    
    # Create orders at adjacent holes with different complexities
    order2_items = [
        OrderItem(name="Hot Dog", quantity=2, complexity='medium', price=8.0),
        OrderItem(name="Beer", quantity=2, complexity='simple', price=6.0)
    ]
    order2 = Order(
        order_id="ORD124", 
        hole_number=5,
        items=order2_items,
        value=sum(item.price * item.quantity for item in order2_items),
        time_of_day='noon'
    )
    
    order3_items = [
        OrderItem(name="Nachos", quantity=1, complexity='complex', price=12.0),
        OrderItem(name="Soda", quantity=2, complexity='simple', price=3.0)
    ]
    order3 = Order(
        order_id="ORD125", 
        hole_number=6,
        items=order3_items,
        value=sum(item.price * item.quantity for item in order3_items),
        time_of_day='noon'
    )
    
    order4_items = [
        OrderItem(name="Sandwich", quantity=1, complexity='medium', price=10.0),
        OrderItem(name="Chips", quantity=1, complexity='simple', price=3.0)
    ]
    order4 = Order(
        order_id="ORD126", 
        hole_number=7,
        items=order4_items,
        value=sum(item.price * item.quantity for item in order4_items),
        time_of_day='noon'
    )
    
    # Add orders to pending list
    dispatcher.add_pending_order(order2)
    dispatcher.add_pending_order(order3)
    dispatcher.add_pending_order(order4)
    
    print(f"\nIncoming orders: Holes {order2.hole_number}, {order3.hole_number}, {order4.hole_number}")
    for order in [order2, order3, order4]:
        print(f"  Order {order.order_id}: ${order.value:.2f} value, {len(order.items)} items")
    
    print("\nDispatching with batching enabled...")
    dispatcher.dispatch_order(order2, consider_batching=True)
    
    # 5. Show final status
    print("\n\n--- Final Asset Status ---")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")
        if asset.current_orders:
            order_ids = [o.order_id for o in asset.current_orders]
            print(f"  → Current orders: {order_ids}")
    
    # 6. Show ML prediction confidence (if available)
    print("\n--- ML Model Confidence ---")
    try:
        ps = dispatcher.prediction_service
        for prediction_type in ['prep_time', 'travel_time', 'acceptance']:
            confidence = ps.get_prediction_confidence(prediction_type)
            print(f"{prediction_type}: {confidence['accuracy']:.1%} accuracy ({confidence['data_points']:,} training samples)")
    except Exception as e:
        print(f"ML confidence data not available: {e}")

if __name__ == "__main__":
    run_simulation() 