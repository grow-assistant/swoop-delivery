"""
Main simulation runner demonstrating the pluggable dispatch strategy system.
"""
from .models import BeverageCart, DeliveryStaff, Order, AssetStatus
from .simulator import GolfCourseSimulator
from .dispatcher_strategies import SimpleDispatcher


def create_test_assets():
    """Create a set of test delivery assets."""
    return [
        BeverageCart(
            asset_id="cart1", 
            name="Reese", 
            loop="front_9", 
            current_location=2
        ),
        BeverageCart(
            asset_id="cart2", 
            name="Bev-Cart 2", 
            loop="back_9", 
            current_location="clubhouse"
        ),
        DeliveryStaff(
            asset_id="staff1", 
            name="Esteban", 
            current_location="clubhouse"
        ),
        DeliveryStaff(
            asset_id="staff2", 
            name="Dylan", 
            current_location=18
        ),
        DeliveryStaff(
            asset_id="staff3", 
            name="Paige", 
            status=AssetStatus.ON_DELIVERY
        )
    ]


def create_test_orders():
    """Create a set of test orders."""
    return [
        Order(order_id="ORD001", hole_number=4),
        Order(order_id="ORD002", hole_number=12),
        Order(order_id="ORD003", hole_number=7),
        Order(order_id="ORD004", hole_number=15),
    ]


def run_simulation():
    """Run the golf course delivery simulation with pluggable dispatch strategies."""
    print("--- Swoop Delivery Simulation for Pinetree Country Club ---")
    print("Demonstrating Pluggable Dispatch Strategy Module")
    
    # Initialize assets
    assets = create_test_assets()
    
    # Create simulator with default SimpleDispatcher strategy
    simulator = GolfCourseSimulator(assets)
    
    # Create test orders
    orders = create_test_orders()
    
    # Run simulation with SimpleDispatcher
    print("\n========== SIMULATION 1: Using SimpleDispatcher ==========")
    simulator.run_scenario(orders[:2])  # Run with first 2 orders
    
    # Reset for next simulation
    simulator.reset()
    
    # Run another scenario with more orders
    print("\n\n========== SIMULATION 2: Multiple Orders ==========")
    simulator.run_scenario(orders)  # Run with all orders
    
    # Demonstrate strategy switching capability
    print("\n\n========== Strategy Switching Capability ==========")
    print("The simulator now supports switching dispatch strategies at runtime.")
    print("You can create custom strategies by extending the DispatchStrategy base class.")
    print("\nExample usage:")
    print("  # Create a custom strategy")
    print("  custom_strategy = MyCustomDispatcher(assets)")
    print("  # Switch to the new strategy")
    print("  simulator.set_dispatch_strategy(custom_strategy)")
    print("  # Run simulation with new strategy")
    print("  simulator.run_scenario(orders)")
    
    print("\n\n========== Key Features Implemented ==========")
    print("✓ Abstract DispatchStrategy base class")
    print("✓ SimpleDispatcher implementation (replicates current logic)")
    print("✓ GolfCourseSimulator using pluggable dispatchers")
    print("✓ Scoring function for asset-order pairs")
    print("✓ Decoupled from hardcoded API endpoints")
    print("✓ True counterfactual simulation environment")


if __name__ == "__main__":
    run_simulation() 