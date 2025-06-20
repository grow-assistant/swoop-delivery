# Task 5: Enhanced Simulation Configuration and Metrics

## Overview
This document describes the enhancements made to the Swoop Delivery simulation system to make it easily configurable and measure the outcomes of different strategies.

## Key Components Implemented

### 1. SimulationConfig (`src/simulation_config.py`)
A comprehensive configuration system that allows easy adjustment of simulation parameters:

- **Simulation Duration**: Configurable runtime (default: 240 minutes)
- **Order Generation**: Adjustable order frequency, variance, and volume multiplier
- **Asset Configuration**: Number of beverage carts and delivery staff
- **Dispatcher Strategy**: Choose from multiple dispatch strategies:
  - `FASTEST_ETA`: Prioritize fastest delivery time
  - `CART_PREFERENCE`: Prefer beverage carts within time window
  - `ZONE_OPTIMAL`: Optimize based on asset zones
  - `BATCH_ORDERS`: Group nearby orders for efficiency
- **Performance Targets**: Set target delivery and wait times

#### Preset Configurations
- **Default**: Balanced configuration for normal operations
- **High Volume**: Increased order frequency and resources
- **Rush Hour**: Very frequent orders with batching strategy
- **Efficiency Test**: Long-duration test with zone optimization

### 2. SimulationSummary (`src/simulation_summary.py`)
A comprehensive metrics collection and analysis system that tracks:

#### Order Metrics
- Order placement time
- Assignment time and wait time
- Delivery time and location
- Batching information

#### Asset Metrics
- Orders delivered per asset
- Utilization rate (active vs idle time)
- Average delivery time
- Distance traveled

#### Key Performance Indicators (KPIs)

**Efficiency Metrics:**
- Average delivery time
- Median delivery time
- Delivery time range and standard deviation
- Asset utilization rate (%)
- Orders delivered per hour

**Quality Metrics:**
- Average customer wait time
- Median customer wait time
- Percentage of orders batched

**Asset-Specific Metrics:**
- Beverage cart vs delivery staff utilization
- Orders delivered by asset type
- Individual asset performance

**Target Achievement:**
- On-time delivery percentage
- On-time wait percentage

### 3. SimulationEngine (`src/simulation_engine.py`)
An event-driven simulation engine that:

- Manages time-based events (orders, deliveries, updates)
- Implements different dispatcher strategies
- Tracks asset movements and status
- Generates comprehensive performance reports
- Supports configurable logging levels

### 4. Enhanced Main Runner (`src/main.py`)
Multiple simulation scenarios:

- **Basic**: Simple demonstration scenario
- **Compare**: Side-by-side strategy comparison
- **Volume**: Tests different order volumes
- **Custom**: Rush hour simulation with detailed logging

## Usage Examples

### Basic Configuration
```python
from src.simulation_config import SimulationConfig
from src.simulation_engine import SimulationEngine

config = SimulationConfig(
    simulation_duration_minutes=60,
    order_generation_interval_min=3.0,
    num_beverage_carts=2,
    num_delivery_staff=3
)

engine = SimulationEngine(config)
summary = engine.run()
```

### Using Presets
```python
from src.simulation_config import SimulationPresets

# Use rush hour preset
config = SimulationPresets.rush_hour()
config.enable_detailed_logging = True

engine = SimulationEngine(config)
summary = engine.run()
```

### Accessing KPIs
```python
# Get KPIs after simulation
kpis = summary.calculate_kpis()
print(f"Average delivery time: {kpis['avg_delivery_time_min']:.1f} minutes")
print(f"Asset utilization: {kpis['avg_asset_utilization_pct']:.1f}%")
print(f"Orders per hour: {kpis['orders_delivered_per_hour']:.1f}")
```

## Running Simulations

### Command Line
```bash
# Run specific scenario
python3 -m src.main basic
python3 -m src.main compare
python3 -m src.main volume
python3 -m src.main custom

# Run all scenarios
python3 -m src.main
```

### Example Script
See `example_usage.py` for detailed examples of:
- Basic simulation setup
- Strategy testing
- Rush hour simulation
- Custom analysis with detailed metrics

## Benefits

1. **Easy Configuration**: Simple parameter adjustment without code changes
2. **Strategy Comparison**: Test different dispatcher strategies to find optimal approach
3. **Performance Analysis**: Comprehensive KPIs to measure effectiveness
4. **Scalability Testing**: Simulate various order volumes and resource levels
5. **Target Tracking**: Monitor achievement of delivery and wait time targets
6. **Detailed Reporting**: Export data for further analysis

## Key Findings from Initial Tests

From the basic simulation run:
- Average delivery time: ~40.8 minutes
- Asset utilization: 54.2%
- Delivery staff utilization (72.3%) higher than cart utilization (27.1%)
- Some orders couldn't be assigned due to all assets being busy
- Zero wait time indicates immediate assignment when assets available

These metrics help identify:
- Need for more assets during peak times
- Opportunity to improve cart utilization
- Potential benefits from order batching strategies