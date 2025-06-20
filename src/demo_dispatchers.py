"""
Demo script showing how to use different dispatch strategies.
"""
from .models import BeverageCart, DeliveryStaff, Order, AssetStatus
from .simulator import GolfCourseSimulator
from .dispatcher_strategies import SimpleDispatcher
from .example_custom_dispatcher import (
    NearestAssetDispatcher, 
    RandomDispatcher, 
    LoadBalancedDispatcher
)


def create_demo_assets():
    """Create a set of demo assets."""
    return [
        BeverageCart(asset_id="cart1", name="Cart Alpha", loop="front_9", current_location=3),
        BeverageCart(asset_id="cart2", name="Cart Beta", loop="back_9", current_location=15),
        DeliveryStaff(asset_id="staff1", name="Staff One", current_location=1),
        DeliveryStaff(asset_id="staff2", name="Staff Two", current_location=10),
    ]


def create_demo_orders():
    """Create a set of demo orders."""
    return [
        Order(order_id="TEST001", hole_number=5),
        Order(order_id="TEST002", hole_number=14),
        Order(order_id="TEST003", hole_number=8),
        Order(order_id="TEST004", hole_number=17),
    ]


def run_dispatcher_comparison():
    """Compare different dispatch strategies on the same scenario."""
    print("=== Pluggable Dispatch Strategy Demonstration ===\n")
    
    # Create assets and orders
    assets = create_demo_assets()
    orders = create_demo_orders()
    
    # Define dispatchers to test
    dispatchers = [
        ("SimpleDispatcher (with cart preference)", SimpleDispatcher),
        ("NearestAssetDispatcher (no cart preference)", NearestAssetDispatcher),
        ("LoadBalancedDispatcher", LoadBalancedDispatcher),
        ("RandomDispatcher (seed=42)", lambda assets: RandomDispatcher(assets, seed=42)),
    ]
    
    # Test each dispatcher
    for dispatcher_name, dispatcher_class in dispatchers:
        print(f"\n{'='*60}")
        print(f"Testing: {dispatcher_name}")
        print('='*60)
        
        # Create simulator with the dispatcher
        simulator = GolfCourseSimulator(
            assets=create_demo_assets(),  # Fresh assets for each test
            dispatch_strategy=dispatcher_class(create_demo_assets())
        )
        
        # Run the scenario
        simulator.run_scenario(orders)
        
        print(f"\nStrategy Performance:")
        print(f"- Average ETA: {simulator.metrics['average_eta']:.2f} minutes" 
              if simulator.metrics['successful_dispatches'] > 0 else "- No successful dispatches")
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)
    print("\nKey Takeaways:")
    print("1. Different strategies produce different dispatch decisions")
    print("2. SimpleDispatcher prefers beverage carts when possible")
    print("3. NearestAssetDispatcher always chooses the closest asset")
    print("4. LoadBalancedDispatcher distributes orders evenly")
    print("5. RandomDispatcher provides a baseline for comparison")
    print("\nYou can easily create your own dispatch strategy by:")
    print("- Extending the DispatchStrategy base class")
    print("- Implementing choose_asset() and score_asset_order_pair()")
    print("- Passing your custom strategy to GolfCourseSimulator")


if __name__ == "__main__":
    run_dispatcher_comparison()