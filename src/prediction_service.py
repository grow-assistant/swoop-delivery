"""
Machine Learning Prediction Service for the delivery system.
This service provides intelligent predictions for order prep time, travel time, and offer acceptance.
"""
import math
import random
from typing import Optional, Tuple, Dict, Any

class PredictionService:
    """
    Service class that simulates ML models for delivery predictions.
    In a real system, these would be trained models using historical data.
    """
    
    def __init__(self):
        # Simulated model parameters (in a real system, these would be learned from data)
        self.base_prep_time_per_item = 2.0  # minutes
        self.prep_time_complexity_factor = {
            'simple': 0.8,     # e.g., bottled drinks
            'medium': 1.0,     # e.g., sandwiches
            'complex': 1.5     # e.g., hot food items
        }
        
        # Travel model parameters
        self.base_travel_time_per_hole = 1.5  # minutes
        self.traffic_patterns = {
            'morning': 0.8,    # Faster in morning
            'noon': 1.2,       # Slower during lunch
            'afternoon': 1.0   # Normal speed
        }
        
        # Acceptance model parameters
        self.base_acceptance_rate = 0.8
        self.distance_penalty_factor = 0.05  # Reduces acceptance by 5% per hole distance
        self.workload_penalty_factor = 0.1   # Reduces acceptance by 10% per active order
    
    def predict_order_prep_time(self, order: Any) -> float:
        """
        Predicts the preparation time for an order based on its contents.
        
        Args:
            order: Order object (should contain items attribute)
        
        Returns:
            Predicted preparation time in minutes
        """
        # If order doesn't have items, return a default time
        if not hasattr(order, 'items') or not order.items:
            return 10.0  # Default fallback
        
        total_prep_time = 0.0
        
        for item in order.items:
            # Get complexity factor (default to medium if not specified)
            complexity = getattr(item, 'complexity', 'medium')
            complexity_factor = self.prep_time_complexity_factor.get(complexity, 1.0)
            
            # Calculate prep time for this item
            item_prep_time = self.base_prep_time_per_item * complexity_factor
            
            # Account for quantity if specified
            quantity = getattr(item, 'quantity', 1)
            item_prep_time *= math.sqrt(quantity)  # Square root to model efficiency of bulk prep
            
            total_prep_time += item_prep_time
        
        # Add some randomness to simulate real-world variation (±20%)
        variation = random.uniform(0.8, 1.2)
        total_prep_time *= variation
        
        # Ensure minimum prep time
        return max(total_prep_time, 2.0)
    
    def predict_travel_time(self, start_location: Any, end_location: Any, 
                          time_of_day: Optional[str] = None) -> float:
        """
        Predicts travel time between two locations on the golf course.
        
        Args:
            start_location: Starting location (hole number or 'clubhouse')
            end_location: Destination location (hole number or 'clubhouse')
            time_of_day: Optional time period ('morning', 'noon', 'afternoon')
        
        Returns:
            Predicted travel time in minutes
        """
        # Convert locations to hole numbers
        start_hole = self._location_to_hole_number(start_location)
        end_hole = self._location_to_hole_number(end_location)
        
        # Calculate base distance
        distance = abs(end_hole - start_hole)
        
        # Base travel time
        base_time = distance * self.base_travel_time_per_hole
        
        # Apply traffic factor if time of day is specified
        traffic_factor = 1.0
        if time_of_day and time_of_day in self.traffic_patterns:
            traffic_factor = self.traffic_patterns[time_of_day]
        
        # Account for terrain difficulty (holes 10-15 are uphill in our simulation)
        terrain_factor = 1.0
        if start_hole >= 10 and start_hole <= 15 and end_hole > start_hole:
            terrain_factor = 1.2  # 20% slower going uphill
        elif end_hole >= 10 and end_hole <= 15 and start_hole > end_hole:
            terrain_factor = 0.9  # 10% faster going downhill
        
        # Calculate final travel time
        travel_time = base_time * traffic_factor * terrain_factor
        
        # Add small random variation (±10%)
        variation = random.uniform(0.9, 1.1)
        travel_time *= variation
        
        # Ensure minimum travel time (even for same location)
        return max(travel_time, 0.5)
    
    def predict_offer_acceptance_chance(self, asset: Any, order: Any) -> float:
        """
        Predicts the probability that an asset will accept a delivery offer.
        
        Args:
            asset: Delivery asset (BeverageCart or DeliveryStaff)
            order: Order to be delivered
        
        Returns:
            Probability of acceptance (0.0 to 1.0)
        """
        acceptance_chance = self.base_acceptance_rate
        
        # Factor 1: Distance penalty
        asset_location = self._location_to_hole_number(asset.current_location)
        order_location = order.hole_number
        distance = abs(order_location - asset_location)
        distance_penalty = distance * self.distance_penalty_factor
        acceptance_chance -= distance_penalty
        
        # Factor 2: Current workload
        current_orders = len(getattr(asset, 'current_orders', []))
        workload_penalty = current_orders * self.workload_penalty_factor
        acceptance_chance -= workload_penalty
        
        # Factor 3: Asset type preference
        # Beverage carts are more likely to accept orders in their zone
        if hasattr(asset, 'loop'):
            if asset.loop == 'front_9' and 1 <= order.hole_number <= 9:
                acceptance_chance += 0.1  # 10% bonus for zone match
            elif asset.loop == 'back_9' and 10 <= order.hole_number <= 18:
                acceptance_chance += 0.1  # 10% bonus for zone match
            else:
                acceptance_chance -= 0.2  # 20% penalty for zone mismatch
        
        # Factor 4: Order value (if available)
        if hasattr(order, 'value'):
            # Higher value orders are more attractive
            if order.value > 50:
                acceptance_chance += 0.1
            elif order.value > 100:
                acceptance_chance += 0.2
        
        # Ensure probability stays within bounds
        return max(0.1, min(1.0, acceptance_chance))
    
    def _location_to_hole_number(self, location: Any) -> int:
        """
        Converts a location to a hole number for distance calculations.
        
        Args:
            location: Location (can be string 'clubhouse' or hole number)
        
        Returns:
            Hole number (0 for clubhouse)
        """
        if isinstance(location, str) and location.lower() == 'clubhouse':
            return 0
        return int(location)
    
    def get_prediction_confidence(self, prediction_type: str) -> Dict[str, float]:
        """
        Returns confidence metrics for different prediction types.
        This simulates model confidence scores.
        
        Args:
            prediction_type: Type of prediction ('prep_time', 'travel_time', 'acceptance')
        
        Returns:
            Dictionary with confidence metrics
        """
        confidence_scores = {
            'prep_time': {
                'accuracy': 0.85,
                'confidence': 0.9,
                'data_points': 10000
            },
            'travel_time': {
                'accuracy': 0.78,
                'confidence': 0.85,
                'data_points': 50000
            },
            'acceptance': {
                'accuracy': 0.72,
                'confidence': 0.8,
                'data_points': 25000
            }
        }
        
        return confidence_scores.get(prediction_type, {
            'accuracy': 0.0,
            'confidence': 0.0,
            'data_points': 0
        })