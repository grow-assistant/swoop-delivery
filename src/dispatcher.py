"""
Core logic for the delivery dispatch system.
"""
import math
import random
from .course_data import COURSE_DATA
from .models import BeverageCart, DeliveryStaff, Order, AssetStatus, OrderStatus
from .prediction_service import PredictionService

# --- NEW CONSTANTS ---
PREP_TIME_MIN = 10
PLAYER_MIN_PER_HOLE = 15  # Average time a player takes to complete a hole
TRAVEL_TIME_PER_HOLE = 1.5 # Travel time for an asset between adjacent holes
BEV_CART_PREFERENCE_MIN = 10 # Preference window for beverage carts

class Dispatcher:
    """Handles the logic for finding and assigning the best delivery candidate."""

    def __init__(self, assets: list):
        self.assets = assets
        self.course_data = COURSE_DATA
        self.prediction_service = PredictionService()

    def _get_location_as_hole_num(self, location):
        """Converts location ('clubhouse' or hole number) to an integer."""
        if isinstance(location, str) and location.lower() == 'clubhouse':
            return 0
        return location

    def calculate_eta_and_destination(self, asset, order: Order):
        """
        Calculates the final ETA and predicted delivery hole for an asset.
        This is an iterative process because the destination depends on the ETA.
        """
        predicted_hole = order.hole_number
        final_eta = float('inf')

        # Iteratively calculate ETA to get a stable prediction. 3 iterations is enough.
        for _ in range(3):
            asset_loc = self._get_location_as_hole_num(asset.current_location)
            
            # Time for asset to get from current location to pickup (clubhouse)
            travel_to_pickup_time = self.prediction_service.predict_travel_time(
                asset.current_location, 'clubhouse', order.time_of_day
            )
            
            # Time for asset to get from pickup to the predicted player location
            travel_from_pickup_time = self.prediction_service.predict_travel_time(
                'clubhouse', predicted_hole, order.time_of_day
            )
            
            # Get predicted prep time based on order contents
            prep_time = self.prediction_service.predict_order_prep_time(order)
            
            # Total time includes prep time and all travel
            total_eta = prep_time + travel_to_pickup_time + travel_from_pickup_time
            
            # Predict how many holes the player has advanced in that time
            holes_advanced = math.floor(total_eta / PLAYER_MIN_PER_HOLE)
            new_predicted_hole = order.hole_number + holes_advanced

            if new_predicted_hole == predicted_hole:
                final_eta = total_eta
                break # Prediction is stable
            
            predicted_hole = new_predicted_hole
            final_eta = total_eta # Update in case loop finishes

        return final_eta, predicted_hole, prep_time

    def find_best_candidate(self, order: Order):
        """
        Finds the best-ranked candidate for a given order, with a preference
        for beverage carts if they are not significantly slower.
        """
        candidates = []

        # 1. Get eligible candidates
        for asset in self.assets:
            if asset.status == AssetStatus.AVAILABLE:
                eta, predicted_hole, prep_time = self.calculate_eta_and_destination(asset, order)
                
                # Check beverage carts for zone restriction
                if isinstance(asset, BeverageCart):
                    order_is_on_front = order.hole_number in self.course_data["front_9_holes"]
                    if (order_is_on_front and asset.loop == "front_9") or \
                       (not order_is_on_front and asset.loop == "back_9"):
                        # Check acceptance probability
                        acceptance_chance = self.prediction_service.predict_offer_acceptance_chance(asset, order)
                        candidates.append({
                            "asset": asset, 
                            "eta": eta, 
                            "predicted_hole": predicted_hole,
                            "prep_time": prep_time,
                            "acceptance_chance": acceptance_chance
                        })
                # Delivery staff have no zone restriction
                elif isinstance(asset, DeliveryStaff):
                    # Check acceptance probability
                    acceptance_chance = self.prediction_service.predict_offer_acceptance_chance(asset, order)
                    candidates.append({
                        "asset": asset, 
                        "eta": eta, 
                        "predicted_hole": predicted_hole,
                        "prep_time": prep_time,
                        "acceptance_chance": acceptance_chance
                    })
        
        # 2. Filter candidates by acceptance probability
        # Only consider candidates with >50% acceptance chance
        viable_candidates = [c for c in candidates if c['acceptance_chance'] > 0.5]
        
        if not viable_candidates:
            # If no one is likely to accept, consider all candidates
            print("(WARNING: No candidates with >50% acceptance chance. Considering all candidates.)")
            viable_candidates = candidates
        
        # 3. Rank candidates with cart preference
        if not viable_candidates:
            return None
        
        # Sort to find the absolute fastest candidate
        viable_candidates.sort(key=lambda x: x["eta"])
        fastest_candidate = viable_candidates[0]

        # Find the best available beverage cart candidate
        cart_candidates = [c for c in viable_candidates if isinstance(c['asset'], BeverageCart)]
        
        if not cart_candidates:
            # No available carts, so return the fastest overall candidate
            return fastest_candidate

        best_cart_candidate = min(cart_candidates, key=lambda x: x['eta'])

        # Prefer the cart if it's not more than 10 minutes slower
        if best_cart_candidate['eta'] <= fastest_candidate['eta'] + BEV_CART_PREFERENCE_MIN:
            print(f"(INFO: Beverage cart preferred. ETA diff: {best_cart_candidate['eta'] - fastest_candidate['eta']:.2f} min)")
            return best_cart_candidate
        else:
            return fastest_candidate

    def dispatch_order(self, order: Order):
        """Assigns an order to the best available candidate."""
        best_candidate_info = self.find_best_candidate(order)
        
        if best_candidate_info:
            best_asset = best_candidate_info["asset"]
            predicted_hole = best_candidate_info['predicted_hole']
            eta = best_candidate_info['eta']
            prep_time = best_candidate_info['prep_time']
            acceptance_chance = best_candidate_info['acceptance_chance']

            # Simulate whether the asset actually accepts the order
            if random.random() <= acceptance_chance:
                order.assigned_to = best_asset
                order.status = OrderStatus.ASSIGNED
                best_asset.status = AssetStatus.ON_DELIVERY
                best_asset.current_orders.append(order)
                
                print(f"Order {order.order_id} for hole {order.hole_number} assigned to {best_asset.name}.")
                print(f"--> Predicted delivery at Hole {predicted_hole} in {eta:.2f} minutes (prep: {prep_time:.1f} min).")
                print(f"--> Acceptance probability was {acceptance_chance:.1%}")
                return best_asset
            else:
                print(f"{best_asset.name} declined the order (acceptance chance was {acceptance_chance:.1%}).")
                # In a real system, we would retry with the next best candidate
                return None
        else:
            print(f"No available candidates found for order {order.order_id}.")
            return None 