#!/usr/bin/env python3
"""
Example usage of the enhanced Swoop Delivery simulation system.
This script demonstrates how to run simulations with different configurations.
"""

from src.simulation_engine import SimulationEngine
from src.simulation_config import SimulationConfig, SimulationPresets, DispatcherStrategy


def example_1_basic_simulation():
    """Example 1: Run a basic simulation with default settings."""
    print("\n" + "="*60)
    print("Example 1: Basic Simulation")
    print("="*60)
    
    # Create a basic configuration
    config = SimulationConfig(
        simulation_duration_minutes=30,  # 30 minute simulation
        order_generation_interval_min=3.0,  # Order every ~3 minutes
        num_beverage_carts=2,
        num_delivery_staff=2,
        enable_detailed_logging=True
    )
    
    # Run simulation
    engine = SimulationEngine(config)
    summary = engine.run()
    
    # Access specific KPIs
    kpis = summary.calculate_kpis()
    print(f"\nKey Results:")
    print(f"- Average delivery time: {kpis['avg_delivery_time_min']:.1f} minutes")
    print(f"- Asset utilization: {kpis['avg_asset_utilization_pct']:.1f}%")
    print(f"- Orders per hour: {kpis['orders_delivered_per_hour']:.1f}")


def example_2_strategy_test():
    """Example 2: Test a specific dispatcher strategy."""
    print("\n" + "="*60)
    print("Example 2: Zone Optimization Strategy")
    print("="*60)
    
    # Configure for zone optimization
    config = SimulationConfig(
        simulation_duration_minutes=60,
        dispatcher_strategy=DispatcherStrategy.ZONE_OPTIMAL,
        order_generation_interval_min=2.5,
        num_beverage_carts=3,
        num_delivery_staff=2,
        enable_detailed_logging=False  # Less verbose output
    )
    
    engine = SimulationEngine(config)
    summary = engine.run()


def example_3_rush_hour():
    """Example 3: Simulate rush hour conditions."""
    print("\n" + "="*60)
    print("Example 3: Rush Hour Simulation")
    print("="*60)
    
    # Use the rush hour preset
    config = SimulationPresets.rush_hour()
    
    # Customize some parameters
    config.simulation_duration_minutes = 45  # 45 minute rush
    config.enable_detailed_logging = True
    
    engine = SimulationEngine(config)
    summary = engine.run()
    
    # Analyze batching effectiveness
    kpis = summary.calculate_kpis()
    print(f"\nBatching Analysis:")
    print(f"- Orders batched: {kpis['percentage_orders_batched']:.1f}%")
    print(f"- Average wait time: {kpis['avg_customer_wait_time_min']:.1f} minutes")


def example_4_custom_analysis():
    """Example 4: Custom analysis with detailed metrics."""
    print("\n" + "="*60)
    print("Example 4: Custom Analysis")
    print("="*60)
    
    # Create a configuration for analysis
    config = SimulationConfig(
        simulation_duration_minutes=120,  # 2 hours
        order_generation_interval_min=4.0,
        dispatcher_strategy=DispatcherStrategy.CART_PREFERENCE,
        cart_preference_window_min=15,  # Increased cart preference window
        target_delivery_time_min=20,  # Aggressive target
        target_wait_time_min=15,
        enable_detailed_logging=False
    )
    
    engine = SimulationEngine(config)
    summary = engine.run()
    
    # Get detailed report
    report = summary.export_detailed_report()
    
    # Analyze cart vs staff performance
    kpis = report['kpis']
    print(f"\nAsset Type Comparison:")
    print(f"- Beverage Cart Orders: {kpis['beverage_cart_orders']}")
    print(f"- Delivery Staff Orders: {kpis['delivery_staff_orders']}")
    print(f"- Cart Utilization: {kpis['beverage_cart_utilization_pct']:.1f}%")
    print(f"- Staff Utilization: {kpis['delivery_staff_utilization_pct']:.1f}%")
    
    # Target achievement
    print(f"\nTarget Achievement:")
    print(f"- On-time deliveries: {kpis['on_time_delivery_pct']:.1f}%")
    print(f"- On-time wait: {kpis['on_time_wait_pct']:.1f}%")


def main():
    """Run all examples."""
    print("Swoop Delivery Simulation Examples")
    print("==================================")
    
    # Run examples
    example_1_basic_simulation()
    example_2_strategy_test()
    example_3_rush_hour()
    example_4_custom_analysis()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()