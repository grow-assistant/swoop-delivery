"""
Main simulation runner for the Swoop Delivery system.
Demonstrates different dispatcher strategies and configuration options.
"""
import sys
from .simulation_engine import SimulationEngine
from .simulation_config import SimulationConfig, SimulationPresets, DispatcherStrategy


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


def main():
    """Main entry point for the simulation."""
    if len(sys.argv) > 1:
        scenario = sys.argv[1].lower()
        
        if scenario == "basic":
            run_basic_scenario()
        elif scenario == "compare":
            run_strategy_comparison()
        elif scenario == "volume":
            run_volume_test()
        elif scenario == "custom":
            run_custom_scenario()
        else:
            print(f"Unknown scenario: {scenario}")
            print("Available scenarios: basic, compare, volume, custom")
    else:
        # Run all scenarios
        print("\nRunning all simulation scenarios...\n")
        run_basic_scenario()
        run_strategy_comparison()
        run_volume_test()
        run_custom_scenario()


if __name__ == "__main__":
    main() 