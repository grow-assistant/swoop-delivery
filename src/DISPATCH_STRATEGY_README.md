# Pluggable Dispatch Strategy Module

## Overview

The pluggable dispatch strategy module decouples the dispatch logic from the main simulation, allowing for testing different dispatching algorithms. This architecture makes the simulation a true "counterfactual" environment where you can experiment with various optimization strategies.

## Architecture

### Core Components

1. **DispatchStrategy (Abstract Base Class)** (`dispatcher_strategies.py`)
   - Defines the interface for all dispatch strategies
   - Abstract methods:
     - `choose_asset()`: Select the best asset for an order
     - `score_asset_order_pair()`: Calculate scoring metrics
   - Common utilities:
     - `get_available_assets()`: Get assets with AVAILABLE status
     - `_get_location_as_hole_num()`: Convert location to hole number

2. **SimpleDispatcher** (`dispatcher_strategies.py`)
   - Replicates the original dispatch logic
   - Features:
     - Prefers beverage carts within a 10-minute window
     - Calculates ETA with player movement prediction
     - Comprehensive scoring function with multiple factors

3. **Dispatcher** (`dispatcher.py`)
   - Main dispatcher that delegates to pluggable strategies
   - Supports runtime strategy switching
   - Handles order assignment and status updates

4. **GolfCourseSimulator** (`simulator.py`)
   - Encapsulates the simulation environment
   - Uses dispatcher strategies for decision making
   - Tracks metrics and performance
   - Supports scenario testing and reset

## Creating Custom Dispatch Strategies

To create your own dispatch strategy:

```python
from src.dispatcher_strategies import DispatchStrategy
from src.models import DeliveryAsset, Order

class MyCustomDispatcher(DispatchStrategy):
    def choose_asset(self, order: Order, available_assets: List[DeliveryAsset]) -> Optional[DeliveryAsset]:
        # Your custom logic here
        pass
    
    def score_asset_order_pair(self, asset: DeliveryAsset, order: Order) -> Dict[str, float]:
        # Return scoring information
        return {
            "final_score": score,
            "eta": estimated_time,
            "predicted_hole": delivery_hole,
            # Add any other metrics you want
        }
```

## Example Strategies

The module includes several example strategies (`example_custom_dispatcher.py`):

1. **NearestAssetDispatcher**: Always chooses the closest asset
2. **RandomDispatcher**: Randomly selects eligible assets (baseline)
3. **LoadBalancedDispatcher**: Distributes orders evenly across assets

## Usage

### Basic Usage

```python
from src.simulator import GolfCourseSimulator
from src.dispatcher_strategies import SimpleDispatcher
from src.models import BeverageCart, DeliveryStaff, Order

# Create assets
assets = [
    BeverageCart(asset_id="cart1", name="Cart 1", loop="front_9"),
    DeliveryStaff(asset_id="staff1", name="Staff 1")
]

# Create simulator with default strategy
simulator = GolfCourseSimulator(assets)

# Process orders
order = Order(order_id="ORD001", hole_number=5)
simulator.process_order(order)
```

### Switching Strategies

```python
from src.example_custom_dispatcher import NearestAssetDispatcher

# Create a custom strategy
custom_strategy = NearestAssetDispatcher(assets)

# Switch to the new strategy
simulator.set_dispatch_strategy(custom_strategy)

# Run simulation with new strategy
simulator.process_order(order)
```

### Running Comparisons

See `demo_dispatchers.py` for a complete example of comparing multiple strategies:

```bash
python3 -m src.demo_dispatchers
```

## Scoring Function

The scoring function is a key component that allows strategies to rank asset-order pairs. The `SimpleDispatcher` uses these factors:

- **ETA Score**: Primary factor (weight: 1.0)
- **Distance Score**: Travel distance to clubhouse (weight: 0.5)
- **Asset Type Score**: Preference for beverage carts (weight: 0.3)
- **Predictability Score**: Uncertainty in delivery prediction (weight: 0.2)

Lower scores indicate better matches.

## Benefits

1. **Modularity**: Easy to swap dispatch strategies without changing core simulation
2. **Testability**: Compare different algorithms on the same scenarios
3. **Extensibility**: Add new strategies without modifying existing code
4. **Experimentation**: True counterfactual environment for optimization
5. **Metrics**: Built-in performance tracking and comparison

## Next Steps

This pluggable architecture is the foundation for building your own "DeepRed" optimization engine. You can:

1. Implement machine learning-based dispatchers
2. Add reinforcement learning strategies
3. Create hybrid approaches combining multiple factors
4. Integrate with external optimization services
5. Build A/B testing frameworks for strategy comparison