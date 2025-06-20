"""
Core logic for the delivery dispatch system.
"""
import math
import random
from .course_data import COURSE_DATA
from .models import BeverageCart, DeliveryStaff, Order, AssetStatus, OrderStatus
from .simulation import AssetSimulator
from .prediction_service import PredictionService

# --- NEW CONSTANTS ---
PREP_TIME_MIN = 10
PLAYER_MIN_PER_HOLE = 15  # Average time a player takes to complete a hole
TRAVEL_TIME_PER_HOLE = 1.5 # Travel time for an asset between adjacent holes
BEV_CART_PREFERENCE_MIN = 10 # Preference window for beverage carts

# --- BATCHING CONSTANTS ---
MAX_BATCH_SIZE = 3  # Maximum number of orders in a batch
ADJACENT_HOLE_THRESHOLD = 2  # Orders within this many holes are considered adjacent
BATCH_DELIVERY_TIME_PENALTY = 2  # Additional minutes per extra order in a batch
BATCH_EFFICIENCY_BONUS = 0.85  # Efficiency multiplier for batched orders (15% reduction in total time)

class Dispatcher:
    """Handles the logic for finding and assigning the best delivery candidate."""

    def __init__(self, assets: list):
        self.assets = assets
        self.course_data = COURSE_DATA
        self.simulator = AssetSimulator()
        self.pending_orders = []  # Store pending orders for batch evaluation
        self.prediction_service = PredictionService()

    def _get_location_as_hole_num(self, location):
        """Converts location ('clubhouse' or hole number) to an integer."""
        if isinstance(location, str) and location.lower() == 'clubhouse':
            return 0
        return location

    def identify_batchable_orders(self, order: Order, available_orders: list = None):
        """
        Identifies orders that can be batched together based on proximity.
        Returns a list of orders that can be batched with the given order.
        """
        if available_orders is None:
            available_orders = [o for o in self.pending_orders if o.status == OrderStatus.PENDING and o != order]
        
        batchable_orders = [order]  # Always include the current order
        
        # Find orders at same or adjacent holes
        for other_order in available_orders:
            if len(batchable_orders) >= MAX_BATCH_SIZE:
                break
                
            # Check if orders are close enough to batch
            hole_distance = abs(other_order.hole_number - order.hole_number)
            if hole_distance <= ADJACENT_HOLE_THRESHOLD:
                batchable_orders.append(other_order)
        
        # Sort by hole number for efficient delivery route
        batchable_orders.sort(key=lambda o: o.hole_number)
        return batchable_orders

    def calculate_batch_eta_and_destinations(self, asset, orders: list):
        """
        Calculates the ETA and destinations for a batch of orders.
        Returns total ETA and a list of (order, predicted_hole) tuples.
        """
        if not orders:
            return float('inf'), []
        
        asset_loc = self._get_location_as_hole_num(asset.current_location)
        
        # Time to get to clubhouse for pickup using ML prediction
        time_of_day = orders[0].time_of_day if orders[0].time_of_day else 'morning'
        travel_to_pickup_time = self.prediction_service.predict_travel_time(
            asset.current_location, 'clubhouse', time_of_day
        )
        
        # Get predicted prep time for all orders combined
        # For batched orders, use the max prep time needed
        max_prep_time = max(self.prediction_service.predict_order_prep_time(order) for order in orders)
        
        # Calculate delivery sequence and times
        destinations = []
        current_time = max_prep_time + travel_to_pickup_time
        last_location = 'clubhouse'  # Starting from clubhouse
        
        for i, order in enumerate(orders):
            # Travel time from last location to this order's predicted location
            travel_time = self.prediction_service.predict_travel_time(
                last_location, order.hole_number, time_of_day
            )
            current_time += travel_time
            
            # Add delivery penalty for each additional order
            if i > 0:
                current_time += BATCH_DELIVERY_TIME_PENALTY
            
            # Predict where the player will be when we arrive
            holes_advanced = math.floor(current_time / PLAYER_MIN_PER_HOLE)
            predicted_hole = order.hole_number + holes_advanced
            
            destinations.append((order, predicted_hole))
            last_location = predicted_hole
        
        # Apply efficiency bonus for batched orders
        if len(orders) > 1:
            current_time *= BATCH_EFFICIENCY_BONUS
        
        return current_time, destinations

    def calculate_eta_and_destination(self, asset, order: Order):
        """
        Calculates the final ETA and predicted delivery hole for an asset.
        This is an iterative process because the destination depends on the ETA.
        """
        predicted_hole = order.hole_number
        final_eta = float('inf')
        time_of_day = order.time_of_day if order.time_of_day else 'morning'

        # Iteratively calculate ETA to get a stable prediction. 3 iterations is enough.
        for _ in range(3):
            asset_loc = self._get_location_as_hole_num(asset.current_location)
            
            # Time for asset to get from current location to pickup (clubhouse)
            travel_to_pickup_time = self.prediction_service.predict_travel_time(
                asset.current_location, 'clubhouse', time_of_day
            )
            
            # Time for asset to get from pickup to the predicted player location
            travel_from_pickup_time = self.prediction_service.predict_travel_time(
                'clubhouse', predicted_hole, time_of_day
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

    def find_best_candidate(self, order: Order, consider_batching: bool = True):
        """
        Finds the best-ranked candidate for a given order, with a preference
        for beverage carts if they are not significantly slower.
        Also evaluates batching opportunities when enabled.
        """
        candidates = []
        batch_candidates = []

        # Identify potential batch orders
        batch_orders = self.identify_batchable_orders(order) if consider_batching else [order]

        # 1. Get eligible candidates for both individual and batched deliveries
        for asset in self.assets:
            if asset.status == AssetStatus.IDLE:
                # Evaluate individual order delivery
                eta, predicted_hole, prep_time = self.calculate_eta_and_destination(asset, order)
                
                # Check beverage carts for zone restriction
                can_deliver = True
                if isinstance(asset, BeverageCart):
                    order_is_on_front = order.hole_number in self.course_data["front_9_holes"]
                    if not ((order_is_on_front and asset.loop == "front_9") or 
                            (not order_is_on_front and asset.loop == "back_9")):
                        can_deliver = False
                
                if can_deliver:
                    # Check acceptance probability
                    acceptance_chance = self.prediction_service.predict_offer_acceptance_chance(asset, order)
                    candidates.append({
                        "asset": asset, 
                        "eta": eta, 
                        "predicted_hole": predicted_hole,
                        "prep_time": prep_time,
                        "acceptance_chance": acceptance_chance,
                        "orders": [order],
                        "is_batch": False
                    })
                    
                    # Evaluate batched delivery if applicable
                    if len(batch_orders) > 1:
                        # Check if all orders in batch can be delivered by this asset
                        can_deliver_batch = True
                        if isinstance(asset, BeverageCart):
                            for batch_order in batch_orders:
                                order_is_on_front = batch_order.hole_number in self.course_data["front_9_holes"]
                                if not ((order_is_on_front and asset.loop == "front_9") or 
                                       (not order_is_on_front and asset.loop == "back_9")):
                                    can_deliver_batch = False
                                    break
                        
                        if can_deliver_batch:
                            batch_eta, batch_destinations = self.calculate_batch_eta_and_destinations(asset, batch_orders)
                            # For batch acceptance, use the average acceptance chance
                            batch_acceptance = sum(self.prediction_service.predict_offer_acceptance_chance(asset, o) 
                                                 for o in batch_orders) / len(batch_orders)
                            batch_candidates.append({
                                "asset": asset,
                                "eta": batch_eta,
                                "destinations": batch_destinations,
                                "orders": batch_orders,
                                "is_batch": True,
                                "acceptance_chance": batch_acceptance
                            })
        
        # 2. Combine and rank all candidates
        all_candidates = candidates + batch_candidates
        
        # Filter candidates by acceptance probability
        # Only consider candidates with >50% acceptance chance
        viable_candidates = [c for c in all_candidates if c['acceptance_chance'] > 0.5]
        
        if not viable_candidates:
            # If no one is likely to accept, consider all candidates
            print("(WARNING: No candidates with >50% acceptance chance. Considering all candidates.)")
            viable_candidates = all_candidates
        
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

    def dispatch_order(self, order: Order, consider_batching: bool = True):
        """Assigns an order to the best available candidate, potentially as part of a batch."""
        best_candidate_info = self.find_best_candidate(order, consider_batching)
        
        if best_candidate_info:
            best_asset = best_candidate_info["asset"]
            orders_to_assign = best_candidate_info["orders"]
            is_batch = best_candidate_info["is_batch"]
            acceptance_chance = best_candidate_info['acceptance_chance']
            
            # Simulate whether the asset actually accepts the order
            if random.random() <= acceptance_chance:
                # Set destination based on first order
                best_asset.destination = orders_to_assign[0].hole_number
                
                # Use the simulator to update asset state properly
                self.simulator.update_asset_state_for_new_order(best_asset, orders_to_assign[0])
                
                # Assign all orders in the batch
                for order_to_assign in orders_to_assign:
                    order_to_assign.assigned_to = best_asset
                    order_to_assign.status = OrderStatus.ASSIGNED
                    if order_to_assign not in best_asset.current_orders:
                        best_asset.current_orders.append(order_to_assign)
                    # Remove from pending orders if it was there
                    if order_to_assign in self.pending_orders:
                        self.pending_orders.remove(order_to_assign)
                
                # Log the assignment
                if is_batch and len(orders_to_assign) > 1:
                    order_ids = ", ".join([o.order_id for o in orders_to_assign])
                    holes = ", ".join([str(o.hole_number) for o in orders_to_assign])
                    print(f"\n=== BATCH DELIVERY ===")
                    print(f"Orders {order_ids} for holes {holes} assigned to {best_asset.name}.")
                    print(f"Batch size: {len(orders_to_assign)} orders")
                    print(f"Acceptance probability was {acceptance_chance:.1%}")
                    
                    # Show delivery sequence
                    destinations = best_candidate_info.get("destinations", [])
                    for i, (batch_order, predicted_hole) in enumerate(destinations):
                        print(f"  → Delivery {i+1}: Order {batch_order.order_id} to Hole {predicted_hole}")
                    
                    print(f"Total batch ETA: {best_candidate_info['eta']:.2f} minutes")
                    
                    # Calculate efficiency gain
                    individual_eta_sum = 0
                    for batch_order in orders_to_assign:
                        ind_eta, _, _ = self.calculate_eta_and_destination(best_asset, batch_order)
                        individual_eta_sum += ind_eta
                    efficiency_gain = (individual_eta_sum - best_candidate_info['eta']) / individual_eta_sum * 100
                    print(f"Efficiency gain: {efficiency_gain:.1f}% time saved vs individual deliveries")
                else:
                    # Single order delivery
                    print(f"\nOrder {order.order_id} for hole {order.hole_number} assigned to {best_asset.name}.")
                    if "predicted_hole" in best_candidate_info:
                        prep_time = best_candidate_info.get('prep_time', PREP_TIME_MIN)
                        print(f"→ Predicted delivery at Hole {best_candidate_info['predicted_hole']} in {best_candidate_info['eta']:.2f} minutes (prep: {prep_time:.1f} min)")
                    print(f"→ Acceptance probability was {acceptance_chance:.1%}")
                
                return best_asset
            else:
                print(f"{best_asset.name} declined the order (acceptance chance was {acceptance_chance:.1%}).")
                # In a real system, we would retry with the next best candidate
                return None
        else:
            print(f"No available candidates found for order {order.order_id}.")
            return None
    
    def add_pending_order(self, order: Order):
        """Adds an order to the pending orders list for potential batching."""
        if order not in self.pending_orders:
            self.pending_orders.append(order)
            print(f"Order {order.order_id} added to pending orders for potential batching.") 