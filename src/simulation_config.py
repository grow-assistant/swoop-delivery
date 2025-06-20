"""
Configuration module for the Swoop Delivery simulation.
Allows easy adjustment of simulation parameters and dispatcher strategies.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any

class DispatcherStrategy(Enum):
    """Available dispatcher strategies."""
    FASTEST_ETA = "fastest_eta"  # Default strategy - prioritize fastest delivery
    CART_PREFERENCE = "cart_preference"  # Prefer beverage carts within time window
    ZONE_OPTIMAL = "zone_optimal"  # Optimize based on asset zones
    BATCH_ORDERS = "batch_orders"  # Group nearby orders for efficiency

@dataclass
class SimulationConfig:
    """Main configuration for the delivery simulation."""
    # Simulation duration
    simulation_duration_minutes: int = 240  # 4 hours
    
    # Order generation parameters
    order_generation_interval_min: float = 5.0  # Average time between orders
    order_generation_variance: float = 2.0  # Variance in order timing
    order_volume_multiplier: float = 1.0  # Multiplier for order volume
    
    # Asset configuration
    num_beverage_carts: int = 2
    num_delivery_staff: int = 3
    
    # Dispatcher configuration
    dispatcher_strategy: DispatcherStrategy = DispatcherStrategy.CART_PREFERENCE
    cart_preference_window_min: int = 10  # Time window for cart preference
    batch_time_window_min: int = 5  # Time window for batching orders
    max_orders_per_batch: int = 3  # Maximum orders per batch
    
    # Course configuration
    front_9_holes: List[int] = field(default_factory=lambda: list(range(1, 10)))
    back_9_holes: List[int] = field(default_factory=lambda: list(range(10, 19)))
    
    # Asset movement parameters
    prep_time_min: int = 10  # Time to prepare order at clubhouse
    travel_time_per_hole: float = 1.5  # Time to travel between adjacent holes
    player_min_per_hole: int = 15  # Average time for player to complete a hole
    
    # Performance thresholds
    target_delivery_time_min: int = 25  # Target delivery time for KPIs
    target_wait_time_min: int = 20  # Target customer wait time
    
    # Logging and output
    enable_detailed_logging: bool = True
    log_interval_minutes: int = 30  # How often to log intermediate stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for easy serialization."""
        return {
            "simulation_duration_minutes": self.simulation_duration_minutes,
            "order_generation_interval_min": self.order_generation_interval_min,
            "order_generation_variance": self.order_generation_variance,
            "order_volume_multiplier": self.order_volume_multiplier,
            "num_beverage_carts": self.num_beverage_carts,
            "num_delivery_staff": self.num_delivery_staff,
            "dispatcher_strategy": self.dispatcher_strategy.value,
            "cart_preference_window_min": self.cart_preference_window_min,
            "batch_time_window_min": self.batch_time_window_min,
            "max_orders_per_batch": self.max_orders_per_batch,
            "prep_time_min": self.prep_time_min,
            "travel_time_per_hole": self.travel_time_per_hole,
            "player_min_per_hole": self.player_min_per_hole,
            "target_delivery_time_min": self.target_delivery_time_min,
            "target_wait_time_min": self.target_wait_time_min,
            "enable_detailed_logging": self.enable_detailed_logging,
            "log_interval_minutes": self.log_interval_minutes
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "SimulationConfig":
        """Create configuration from dictionary."""
        if "dispatcher_strategy" in config_dict:
            config_dict["dispatcher_strategy"] = DispatcherStrategy(config_dict["dispatcher_strategy"])
        return cls(**config_dict)

# Preset configurations for common scenarios
class SimulationPresets:
    """Common simulation presets for testing different scenarios."""
    
    @staticmethod
    def default() -> SimulationConfig:
        """Default balanced configuration."""
        return SimulationConfig()
    
    @staticmethod
    def high_volume() -> SimulationConfig:
        """High order volume configuration."""
        return SimulationConfig(
            order_generation_interval_min=2.5,
            order_generation_variance=1.0,
            order_volume_multiplier=2.0,
            num_beverage_carts=3,
            num_delivery_staff=4
        )
    
    @staticmethod
    def rush_hour() -> SimulationConfig:
        """Rush hour scenario with very frequent orders."""
        return SimulationConfig(
            simulation_duration_minutes=120,  # 2 hour rush
            order_generation_interval_min=1.5,
            order_generation_variance=0.5,
            order_volume_multiplier=3.0,
            dispatcher_strategy=DispatcherStrategy.BATCH_ORDERS,
            batch_time_window_min=3,
            max_orders_per_batch=4
        )
    
    @staticmethod
    def efficiency_test() -> SimulationConfig:
        """Configuration to test dispatcher efficiency."""
        return SimulationConfig(
            simulation_duration_minutes=480,  # 8 hours
            order_generation_interval_min=4.0,
            dispatcher_strategy=DispatcherStrategy.ZONE_OPTIMAL,
            target_delivery_time_min=20,
            target_wait_time_min=15
        )