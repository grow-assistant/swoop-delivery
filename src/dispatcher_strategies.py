"""
Pluggable dispatcher strategies for the delivery system.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Tuple
import math

from .models import BeverageCart, DeliveryStaff, Order, AssetStatus, DeliveryAsset
from .course_data import COURSE_DATA

# Constants for dispatch calculations
PREP_TIME_MIN = 10
PLAYER_MIN_PER_HOLE = 15  
TRAVEL_TIME_PER_HOLE = 1.5 
BEV_CART_PREFERENCE_MIN = 10 


class DispatchStrategy(ABC):
    """Abstract base class for dispatch strategies."""
    
    def __init__(self, assets: List[DeliveryAsset]):
        self.assets = assets
        self.course_data = COURSE_DATA
    
    @abstractmethod
    def choose_asset(self, order: Order, available_assets: List[DeliveryAsset]) -> Optional[DeliveryAsset]:
        """
        Choose the best asset for the given order from available assets.
        
        Args:
            order: The order to be dispatched
            available_assets: List of assets with AVAILABLE status
            
        Returns:
            The chosen DeliveryAsset or None if no suitable asset found
        """
        pass
    
    @abstractmethod
    def score_asset_order_pair(self, asset: DeliveryAsset, order: Order) -> Dict[str, float]:
        """
        Calculate a score for how well an asset matches an order.
        
        Args:
            asset: The delivery asset to score
            order: The order to be delivered
            
        Returns:
            Dictionary containing score components and final score
        """
        pass
    
    def get_available_assets(self) -> List[DeliveryAsset]:
        """Get all assets with AVAILABLE status."""
        return [asset for asset in self.assets if asset.status == AssetStatus.AVAILABLE]
    
    def _get_location_as_hole_num(self, location):
        """Converts location ('clubhouse' or hole number) to an integer."""
        if isinstance(location, str) and location.lower() == 'clubhouse':
            return 0
        return location


class SimpleDispatcher(DispatchStrategy):
    """
    Simple dispatcher that replicates the current dispatch logic.
    Finds the nearest available asset with preference for beverage carts.
    """
    
    def choose_asset(self, order: Order, available_assets: List[DeliveryAsset]) -> Optional[DeliveryAsset]:
        """
        Choose the best asset based on ETA with preference for beverage carts.
        """
        if not available_assets:
            return None
            
        candidates = []
        
        # Evaluate each available asset
        for asset in available_assets:
            # Check if asset is eligible
            if not self._is_asset_eligible(asset, order):
                continue
                
            # Calculate metrics
            eta, predicted_hole = self.calculate_eta_and_destination(asset, order.hole_number)
            score_data = self.score_asset_order_pair(asset, order)
            
            candidates.append({
                "asset": asset,
                "eta": eta,
                "predicted_hole": predicted_hole,
                "score": score_data["final_score"],
                "score_data": score_data
            })
        
        if not candidates:
            return None
        
        # Sort by ETA to find fastest
        candidates.sort(key=lambda x: x["eta"])
        fastest_candidate = candidates[0]
        
        # Find best beverage cart
        cart_candidates = [c for c in candidates if isinstance(c['asset'], BeverageCart)]
        
        if not cart_candidates:
            return fastest_candidate["asset"]
        
        best_cart_candidate = min(cart_candidates, key=lambda x: x['eta'])
        
        # Prefer cart if within preference window
        if best_cart_candidate['eta'] <= fastest_candidate['eta'] + BEV_CART_PREFERENCE_MIN:
            print(f"(INFO: Beverage cart preferred. ETA diff: {best_cart_candidate['eta'] - fastest_candidate['eta']:.2f} min)")
            return best_cart_candidate["asset"]
        else:
            return fastest_candidate["asset"]
    
    def score_asset_order_pair(self, asset: DeliveryAsset, order: Order) -> Dict[str, float]:
        """
        Score an asset-order pair based on multiple factors.
        Lower scores are better.
        """
        eta, predicted_hole = self.calculate_eta_and_destination(asset, order.hole_number)
        
        # Score components
        eta_score = eta  # Lower ETA is better
        
        # Distance score (how far the asset needs to travel)
        asset_loc = self._get_location_as_hole_num(asset.current_location)
        distance_score = abs(asset_loc - 0) * TRAVEL_TIME_PER_HOLE
        
        # Asset type score (preference for beverage carts)
        asset_type_score = 0 if isinstance(asset, BeverageCart) else 5
        
        # Predictability score (how far ahead we're predicting)
        predictability_score = abs(predicted_hole - order.hole_number) * 2
        
        # Calculate final score (weighted combination)
        final_score = (
            eta_score * 1.0 +  # ETA is primary factor
            distance_score * 0.5 +  # Distance matters but less than ETA
            asset_type_score * 0.3 +  # Slight preference for carts
            predictability_score * 0.2  # Slight penalty for uncertain predictions
        )
        
        return {
            "eta": eta,
            "predicted_hole": predicted_hole,
            "eta_score": eta_score,
            "distance_score": distance_score,
            "asset_type_score": asset_type_score,
            "predictability_score": predictability_score,
            "final_score": final_score
        }
    
    def _is_asset_eligible(self, asset: DeliveryAsset, order: Order) -> bool:
        """Check if an asset is eligible to handle an order."""
        # Beverage carts have zone restrictions
        if isinstance(asset, BeverageCart):
            order_is_on_front = order.hole_number in self.course_data["front_9_holes"]
            if order_is_on_front and asset.loop != "front_9":
                return False
            if not order_is_on_front and asset.loop != "back_9":
                return False
        
        return True
    
    def calculate_eta_and_destination(self, asset: DeliveryAsset, order_hole: int) -> Tuple[float, int]:
        """
        Calculate the final ETA and predicted delivery hole for an asset.
        """
        predicted_hole = order_hole
        final_eta = float('inf')
        
        # Iteratively calculate ETA to get a stable prediction
        for _ in range(3):
            asset_loc = self._get_location_as_hole_num(asset.current_location)
            
            # Time for asset to get from current location to pickup (clubhouse)
            travel_to_pickup_time = abs(asset_loc - 0) * TRAVEL_TIME_PER_HOLE
            
            # Time for asset to get from pickup to the predicted player location
            travel_from_pickup_time = abs(predicted_hole - 0) * TRAVEL_TIME_PER_HOLE
            
            # Total time includes prep time and all travel
            total_eta = PREP_TIME_MIN + travel_to_pickup_time + travel_from_pickup_time
            
            # Predict how many holes the player has advanced in that time
            holes_advanced = math.floor(total_eta / PLAYER_MIN_PER_HOLE)
            new_predicted_hole = order_hole + holes_advanced
            
            if new_predicted_hole == predicted_hole:
                final_eta = total_eta
                break
            
            predicted_hole = new_predicted_hole
            final_eta = total_eta
        
        return final_eta, predicted_hole