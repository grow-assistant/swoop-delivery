"""
Example custom dispatcher strategies to demonstrate the pluggable architecture.
"""
from typing import List, Optional, Dict
import random

from .dispatcher_strategies import DispatchStrategy
from .models import DeliveryAsset, Order, BeverageCart, DeliveryStaff


class NearestAssetDispatcher(DispatchStrategy):
    """
    A dispatcher that always chooses the nearest available asset,
    regardless of asset type (no preference for beverage carts).
    """
    
    def choose_asset(self, order: Order, available_assets: List[DeliveryAsset]) -> Optional[DeliveryAsset]:
        """Choose the nearest asset based purely on distance."""
        if not available_assets:
            return None
        
        best_asset = None
        min_distance = float('inf')
        
        for asset in available_assets:
            if not self._is_asset_eligible(asset, order):
                continue
            
            # Calculate distance from asset to clubhouse
            asset_loc = self._get_location_as_hole_num(asset.current_location)
            distance = abs(int(asset_loc) - 0)  # Distance to clubhouse
            
            if distance < min_distance:
                min_distance = distance
                best_asset = asset
        
        return best_asset
    
    def score_asset_order_pair(self, asset: DeliveryAsset, order: Order) -> Dict[str, float]:
        """Score based purely on distance."""
        asset_loc = self._get_location_as_hole_num(asset.current_location)
        distance = abs(int(asset_loc) - 0)
        
        return {
            "distance": distance,
            "final_score": distance,
            "eta": distance * 1.5 + 10,  # Simplified ETA calculation
            "predicted_hole": order.hole_number
        }
    
    def _is_asset_eligible(self, asset: DeliveryAsset, order: Order) -> bool:
        """Check zone restrictions for beverage carts."""
        if isinstance(asset, BeverageCart):
            order_is_on_front = order.hole_number in self.course_data["front_9_holes"]
            if order_is_on_front and asset.loop != "front_9":
                return False
            if not order_is_on_front and asset.loop != "back_9":
                return False
        return True


class RandomDispatcher(DispatchStrategy):
    """
    A dispatcher that randomly selects from available eligible assets.
    Useful for testing and establishing baseline performance.
    """
    
    def __init__(self, assets: List[DeliveryAsset], seed: Optional[int] = None):
        super().__init__(assets)
        if seed is not None:
            random.seed(seed)
    
    def choose_asset(self, order: Order, available_assets: List[DeliveryAsset]) -> Optional[DeliveryAsset]:
        """Randomly choose from eligible assets."""
        eligible_assets = [
            asset for asset in available_assets 
            if self._is_asset_eligible(asset, order)
        ]
        
        if not eligible_assets:
            return None
        
        return random.choice(eligible_assets)
    
    def score_asset_order_pair(self, asset: DeliveryAsset, order: Order) -> Dict[str, float]:
        """Random scoring - all assets get the same score."""
        return {
            "random_score": 1.0,
            "final_score": 1.0,
            "eta": 25.0,  # Default ETA
            "predicted_hole": order.hole_number + 1
        }
    
    def _is_asset_eligible(self, asset: DeliveryAsset, order: Order) -> bool:
        """Check zone restrictions for beverage carts."""
        if isinstance(asset, BeverageCart):
            order_is_on_front = order.hole_number in self.course_data["front_9_holes"]
            if order_is_on_front and asset.loop != "front_9":
                return False
            if not order_is_on_front and asset.loop != "back_9":
                return False
        return True


class LoadBalancedDispatcher(DispatchStrategy):
    """
    A dispatcher that tries to balance the load across all assets.
    Prefers assets with fewer current orders.
    """
    
    def choose_asset(self, order: Order, available_assets: List[DeliveryAsset]) -> Optional[DeliveryAsset]:
        """Choose asset with the least number of current orders."""
        eligible_assets = [
            asset for asset in available_assets 
            if self._is_asset_eligible(asset, order)
        ]
        
        if not eligible_assets:
            return None
        
        # Sort by number of current orders (ascending)
        eligible_assets.sort(key=lambda a: len(a.current_orders))
        
        # Among assets with the same load, prefer the nearest
        min_orders = len(eligible_assets[0].current_orders)
        least_loaded = [a for a in eligible_assets if len(a.current_orders) == min_orders]
        
        # Choose nearest among least loaded
        best_asset = min(least_loaded, 
                        key=lambda a: abs(int(self._get_location_as_hole_num(a.current_location)) - 0))
        
        return best_asset
    
    def score_asset_order_pair(self, asset: DeliveryAsset, order: Order) -> Dict[str, float]:
        """Score based on current load and distance."""
        asset_loc = self._get_location_as_hole_num(asset.current_location)
        distance = abs(int(asset_loc) - 0)
        load_score = len(asset.current_orders) * 10  # Penalty for each current order
        
        final_score = distance + load_score
        
        return {
            "distance": distance,
            "load": len(asset.current_orders),
            "load_score": load_score,
            "final_score": final_score,
            "eta": distance * 1.5 + 10 + load_score,
            "predicted_hole": order.hole_number + 1
        }
    
    def _is_asset_eligible(self, asset: DeliveryAsset, order: Order) -> bool:
        """Check zone restrictions for beverage carts."""
        if isinstance(asset, BeverageCart):
            order_is_on_front = order.hole_number in self.course_data["front_9_holes"]
            if order_is_on_front and asset.loop != "front_9":
                return False
            if not order_is_on_front and asset.loop != "back_9":
                return False
        return True