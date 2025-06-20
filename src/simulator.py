"""
Golf Course Simulator for testing different dispatch strategies.
"""
from typing import List, Optional
from .models import DeliveryAsset, Order, AssetStatus, BeverageCart
from .dispatcher import Dispatcher
from .dispatcher_strategies import DispatchStrategy


class GolfCourseSimulator:
    """
    Simulator for the golf course delivery system.
    Allows testing different dispatch strategies in a counterfactual environment.
    """
    
    def __init__(self, assets: List[DeliveryAsset], dispatch_strategy: Optional[DispatchStrategy] = None):
        """
        Initialize the simulator with assets and dispatch strategy.
        
        Args:
            assets: List of delivery assets
            dispatch_strategy: Strategy to use for dispatching. 
                             If None, uses SimpleDispatcher by default.
        """
        self.assets = assets
        self.dispatcher = Dispatcher(assets, dispatch_strategy)
        self.orders_processed = []
        self.metrics = {
            "total_orders": 0,
            "successful_dispatches": 0,
            "failed_dispatches": 0,
            "total_eta": 0.0,
            "average_eta": 0.0
        }
    
    def set_dispatch_strategy(self, strategy: DispatchStrategy):
        """Change the dispatch strategy at runtime."""
        self.dispatcher.set_strategy(strategy)
    
    def process_order(self, order: Order):
        """
        Process a single order through the simulation.
        
        Args:
            order: The order to process
            
        Returns:
            The assigned asset or None if dispatch failed
        """
        print(f"\n--- Processing Order {order.order_id} ---")
        print(f"Order for hole {order.hole_number}")
        
        # Dispatch the order
        assigned_asset = self.dispatcher.dispatch_order(order)
        
        # Update metrics
        self.metrics["total_orders"] += 1
        if assigned_asset:
            self.metrics["successful_dispatches"] += 1
            # Get ETA from the strategy's scoring
            score_info = self.dispatcher.strategy.score_asset_order_pair(assigned_asset, order)
            self.metrics["total_eta"] += score_info["eta"]
        else:
            self.metrics["failed_dispatches"] += 1
        
        # Store order for analysis
        self.orders_processed.append(order)
        
        return assigned_asset
    
    def run_scenario(self, orders: List[Order]):
        """
        Run a complete scenario with multiple orders.
        
        Args:
            orders: List of orders to process
        """
        print("\n=== Starting Golf Course Delivery Simulation ===")
        self.print_asset_status()
        
        for order in orders:
            self.process_order(order)
        
        self.print_simulation_summary()
    
    def print_asset_status(self):
        """Print the current status of all assets."""
        print("\nCurrent Asset Status:")
        for asset in self.assets:
            location = asset.current_location
            if isinstance(asset, BeverageCart):
                print(f"- {asset.name} ({asset.__class__.__name__}): "
                      f"Location={location}, Status={asset.status.value}, Loop={asset.loop}")
            else:
                print(f"- {asset.name} ({asset.__class__.__name__}): "
                      f"Location={location}, Status={asset.status.value}")
    
    def print_simulation_summary(self):
        """Print a summary of the simulation results."""
        print("\n=== Simulation Summary ===")
        print(f"Total Orders: {self.metrics['total_orders']}")
        print(f"Successful Dispatches: {self.metrics['successful_dispatches']}")
        print(f"Failed Dispatches: {self.metrics['failed_dispatches']}")
        
        if self.metrics['successful_dispatches'] > 0:
            self.metrics['average_eta'] = self.metrics['total_eta'] / self.metrics['successful_dispatches']
            print(f"Average ETA: {self.metrics['average_eta']:.2f} minutes")
        
        # Success rate
        if self.metrics['total_orders'] > 0:
            success_rate = (self.metrics['successful_dispatches'] / self.metrics['total_orders']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        # Final asset status
        print("\nFinal Asset Status:")
        self.print_asset_status()
    
    def reset(self):
        """Reset the simulation state."""
        # Reset all assets to available status at clubhouse
        for asset in self.assets:
            asset.status = AssetStatus.AVAILABLE
            asset.current_location = "clubhouse"
            asset.current_orders = []
        
        # Reset metrics
        self.orders_processed = []
        self.metrics = {
            "total_orders": 0,
            "successful_dispatches": 0,
            "failed_dispatches": 0,
            "total_eta": 0.0,
            "average_eta": 0.0
        }