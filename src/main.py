"""
Main simulation runner for the Swoop Delivery system.
Demonstrates different dispatcher strategies and configuration options.
"""
import sys
from .simulation_engine import SimulationEngine
from .simulation_config import SimulationConfig, SimulationPresets, DispatcherStrategy
from .models import BeverageCart, DeliveryStaff, Order, OrderItem, AssetStatus
from .dispatcher import Dispatcher
from .simulation import AssetSimulator


def run_simple_simulation():
    """Original simple simulation for backward compatibility."""
    print("--- Swoop Delivery Simulation for Pinetree Country Club ---")
    
    # 1. Initialize Delivery Assets
    assets = [
        BeverageCart(asset_id="cart1", name="Reese", loop="front_9", current_location=2),
        BeverageCart(asset_id="cart2", name="Bev-Cart 2", loop="back_9", current_location="clubhouse"),
        DeliveryStaff(asset_id="staff1", name="Esteban", current_location="clubhouse"),
        DeliveryStaff(asset_id="staff2", name="Dylan", current_location=18),
        DeliveryStaff(asset_id="staff3", name="Paige", status=AssetStatus.EN_ROUTE_TO_DROPOFF, destination=15)
    ]
    
    print("\nInitial Asset Status:")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")
        
    # 2. Initialize Dispatcher and Simulator
    dispatcher = Dispatcher(assets)
    simulator = AssetSimulator()
    
    # 3. Create a new order
    print("\n--- New Order ---")
    order = Order(order_id="ORD123", hole_number=4)
    print(f"Incoming order for Hole {order.hole_number}.")

    # 4. Dispatch the order
    print("\nDispatching order...")
    dispatcher.dispatch_order(order)
    
    # 5. Simulate one movement step to show state-driven behavior
    print("\n--- Simulating Asset Movement ---")
    for asset in assets:
        simulator.simulate_asset_movement(asset)
    
    # 6. Show updated status
    print("\nUpdated Asset Status:")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")
        if asset.destination:
            print(f"  -> Heading to: {asset.destination}")


def run_basic_scenario():
    """Run a basic simulation scenario."""
    print("\n" + "="*80)
    print("BASIC SIMULATION SCENARIO")
    print("="*80)
    
    # Use default configuration
    config = SimulationPresets.default()
    config.simulation_duration_minutes = 60  # 1 hour for demo
    config.enable_detailed_logging = False  # Less verbose
    
    engine = SimulationEngine(config)
    summary = engine.run()
    
    return summary


def run_strategy_comparison():
    """Compare different dispatcher strategies."""
    print("\n" + "="*80)
    print("STRATEGY COMPARISON")
    print("="*80)
    
    strategies = [
        DispatcherStrategy.FASTEST_ETA,
        DispatcherStrategy.CART_PREFERENCE,
        DispatcherStrategy.ZONE_OPTIMAL,
    ]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n\n{'#'*60}")
        print(f"Testing Strategy: {strategy.value}")
        print(f"{'#'*60}")
        
        config = SimulationConfig(
            simulation_duration_minutes=120,  # 2 hours
            dispatcher_strategy=strategy,
            enable_detailed_logging=False,
            order_generation_interval_min=4.0,
            num_beverage_carts=2,
            num_delivery_staff=3
        )
        
        engine = SimulationEngine(config)
        summary = engine.run()
        
        # Store key metrics
        kpis = summary.calculate_kpis()
        results[strategy.value] = {
            "avg_delivery_time": kpis.get("avg_delivery_time_min", 0),
            "avg_wait_time": kpis.get("avg_customer_wait_time_min", 0),
            "utilization": kpis.get("avg_asset_utilization_pct", 0),
            "orders_per_hour": kpis.get("orders_delivered_per_hour", 0),
            "cart_utilization": kpis.get("beverage_cart_utilization_pct", 0),
            "staff_utilization": kpis.get("delivery_staff_utilization_pct", 0)
        }
    
    # Print comparison
    print("\n\n" + "="*80)
    print("STRATEGY COMPARISON RESULTS")
    print("="*80)
    print(f"\n{'Strategy':<20} {'Avg Delivery':<15} {'Avg Wait':<12} {'Utilization':<12} {'Orders/Hr':<10}")
    print(f"{'':<20} {'(minutes)':<15} {'(minutes)':<12} {'(%)':<12} {'':<10}")
    print("-"*80)
    
    for strategy, metrics in results.items():
        print(f"{strategy:<20} {metrics['avg_delivery_time']:>12.1f} {metrics['avg_wait_time']:>12.1f} "
              f"{metrics['utilization']:>12.1f} {metrics['orders_per_hour']:>10.1f}")
    
    print(f"\n{'Strategy':<20} {'Cart Util %':<15} {'Staff Util %':<15}")
    print("-"*60)
    for strategy, metrics in results.items():
        print(f"{strategy:<20} {metrics['cart_utilization']:>12.1f} {metrics['staff_utilization']:>15.1f}")


def run_volume_test():
    """Test system under different order volumes."""
    print("\n" + "="*80)
    print("VOLUME STRESS TEST")
    print("="*80)
    
    volumes = [
        ("Low Volume", 0.5),
        ("Normal Volume", 1.0),
        ("High Volume", 2.0),
        ("Rush Hour", 3.0)
    ]
    
    for name, multiplier in volumes:
        print(f"\n\n{'#'*60}")
        print(f"Testing: {name} (Multiplier: {multiplier}x)")
        print(f"{'#'*60}")
        
        config = SimulationConfig(
            simulation_duration_minutes=60,
            order_volume_multiplier=multiplier,
            dispatcher_strategy=DispatcherStrategy.CART_PREFERENCE,
            enable_detailed_logging=False
        )
        
        # Adjust resources for higher volumes
        if multiplier >= 2.0:
            config.num_beverage_carts = 3
            config.num_delivery_staff = 4
        
        engine = SimulationEngine(config)
        summary = engine.run()


def run_custom_scenario():
    """Run a custom configurable scenario."""
    print("\n" + "="*80)
    print("CUSTOM SCENARIO - RUSH HOUR SIMULATION")
    print("="*80)
    
    # Use rush hour preset
    config = SimulationPresets.rush_hour()
    config.enable_detailed_logging = True  # Show detailed logs
    
    engine = SimulationEngine(config)
    summary = engine.run()
    
    # Export detailed report
    report = summary.export_detailed_report()
    print(f"\nDetailed report contains {len(report['orders'])} orders and {len(report['events'])} events")


def run_ml_demo():
    """Demonstrates the ML prediction service with manual order dispatch."""
    print("\n" + "="*80)
    print("ML PREDICTION SERVICE DEMO")
    print("="*80)
    print("--- Swoop Delivery Simulation for Pinetree Country Club ---")
    print("--- Now powered by ML Prediction Service with Batch Order Support ---")
    
    # 1. Initialize Delivery Assets
    assets = [
        BeverageCart(asset_id="cart1", name="Reese", loop="front_9", current_location=2),
        BeverageCart(asset_id="cart2", name="Bev-Cart 2", loop="back_9", current_location="clubhouse"),
        DeliveryStaff(asset_id="staff1", name="Esteban", current_location="clubhouse"),
        DeliveryStaff(asset_id="staff2", name="Dylan", current_location=18),
        DeliveryStaff(asset_id="staff3", name="Paige", status=AssetStatus.EN_ROUTE_TO_DROPOFF, destination=15)
    ]
    
    print("\nInitial Asset Status:")
    for asset in assets:
        print(f"- {asset.name}: Location={asset.current_location}, Status={asset.status.value}")
        
    # 2. Initialize Dispatcher and Simulator
    dispatcher = Dispatcher(assets)
    simulator = AssetSimulator()
    
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
            asset.status = AssetStatus.IDLE
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


def main():
    """Main entry point for the simulation."""
    if len(sys.argv) > 1:
        scenario = sys.argv[1].lower()
        
        if scenario == "simple":
            run_simple_simulation()
        elif scenario == "basic":
            run_basic_scenario()
        elif scenario == "compare":
            run_strategy_comparison()
        elif scenario == "volume":
            run_volume_test()
        elif scenario == "custom":
            run_custom_scenario()
        elif scenario == "ml-demo":
            run_ml_demo()
        else:
            print(f"Unknown scenario: {scenario}")
            print("Available scenarios: simple, basic, compare, volume, custom, ml-demo")
    else:
        # Run the simple simulation by default
        run_simple_simulation()


if __name__ == "__main__":
    main() 