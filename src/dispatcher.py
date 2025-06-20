"""
Core dispatcher system that uses pluggable strategies.
"""
from typing import Optional
from .models import Order, AssetStatus
from .dispatcher_strategies import DispatchStrategy, SimpleDispatcher


class Dispatcher:
    """
    Main dispatcher that delegates to pluggable dispatch strategies.
    """
    
    def __init__(self, assets: list, strategy: Optional[DispatchStrategy] = None):
        """
        Initialize dispatcher with assets and a strategy.
        
        Args:
            assets: List of delivery assets
            strategy: Dispatch strategy to use. Defaults to SimpleDispatcher.
        """
        self.assets = assets
        self.strategy = strategy or SimpleDispatcher(assets)
    
    def set_strategy(self, strategy: DispatchStrategy):
        """Change the dispatch strategy at runtime."""
        self.strategy = strategy
    
    def dispatch_order(self, order: Order):
        """
        Dispatch an order using the current strategy.
        
        Args:
            order: The order to dispatch
            
        Returns:
            The assigned asset or None if no asset was available
        """
        # Get available assets
        available_assets = self.strategy.get_available_assets()
        
        if not available_assets:
            print(f"No available assets for order {order.order_id}.")
            return None
        
        # Use the strategy to choose the best asset
        chosen_asset = self.strategy.choose_asset(order, available_assets)
        
        if chosen_asset:
            # Get scoring information for logging
            score_info = self.strategy.score_asset_order_pair(chosen_asset, order)
            
            # Assign the order
            order.assigned_to = chosen_asset
            order.status = "assigned"
            chosen_asset.status = AssetStatus.ON_DELIVERY
            chosen_asset.current_orders.append(order)
            
            print(f"Order {order.order_id} for hole {order.hole_number} assigned to {chosen_asset.name}.")
            eta = score_info.get('eta', 0)
            predicted_hole = score_info.get('predicted_hole', order.hole_number)
            print(f"--> Predicted delivery at Hole {predicted_hole} in {eta:.2f} minutes (includes 10 min prep time).")
            
            # Print detailed scoring information if available
            if all(key in score_info for key in ['eta_score', 'distance_score', 'asset_type_score', 'predictability_score']):
                print(f"    Score Details: Final Score={score_info['final_score']:.2f}, "
                      f"ETA={score_info['eta_score']:.2f}, Distance={score_info['distance_score']:.2f}, "
                      f"Asset Type={score_info['asset_type_score']:.2f}, Predictability={score_info['predictability_score']:.2f}")
            else:
                # Print available score information
                print(f"    Score: {score_info.get('final_score', 'N/A')}")
            
            return chosen_asset
        else:
            print(f"No suitable candidates found for order {order.order_id}.")
            return None 