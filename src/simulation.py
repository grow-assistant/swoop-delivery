"""
Asset movement simulation module for realistic delivery simulations.
"""
import random
from typing import Union
from .models import BeverageCart, DeliveryStaff, AssetStatus, Order
from .course_data import COURSE_DATA


class AssetSimulator:
    """Handles realistic movement simulation for delivery assets."""
    
    def __init__(self):
        self.course_data = COURSE_DATA
        
    def _get_location_as_hole_num(self, location: Union[str, int]) -> int:
        """Converts location ('clubhouse' or hole number) to an integer."""
        if isinstance(location, str) and location.lower() == 'clubhouse':
            return 0
        return int(location)
    
    def _move_towards_destination(self, current_location: Union[str, int], 
                                 destination: Union[str, int], 
                                 max_holes_per_move: int = 3) -> Union[str, int]:
        """
        Move an asset towards its destination.
        Returns the new location after movement.
        """
        current = self._get_location_as_hole_num(current_location)
        dest = self._get_location_as_hole_num(destination)
        
        if current == dest:
            return destination
            
        # Calculate direction and distance
        if dest > current:
            # Moving forward
            move_distance = min(dest - current, max_holes_per_move)
            new_location = current + move_distance
        else:
            # Moving backward
            move_distance = min(current - dest, max_holes_per_move)
            new_location = current - move_distance
            
        # Convert back to appropriate format
        if new_location == 0:
            return "clubhouse"
        return new_location
    
    def get_next_realistic_location(self, asset: Union[BeverageCart, DeliveryStaff]) -> Union[str, int]:
        """
        Get a realistic next location for an IDLE asset.
        This simulates an asset repositioning themselves for future orders.
        """
        current = self._get_location_as_hole_num(asset.current_location)
        
        # For beverage carts, stay within their loop
        if isinstance(asset, BeverageCart):
            if asset.loop == "front_9":
                # Can move within holes 1-9
                possible_holes = list(range(1, 10))
            else:  # back_9
                # Can move within holes 10-18
                possible_holes = list(range(10, 19))
            
            # Remove current location and nearby holes to encourage movement
            possible_holes = [h for h in possible_holes if abs(h - current) > 1]
            
            if possible_holes:
                # Weight selection towards middle of the loop for better coverage
                if asset.loop == "front_9":
                    weights = [abs(h - 5) + 1 for h in possible_holes]  # Weight towards hole 5
                else:
                    weights = [abs(h - 14) + 1 for h in possible_holes]  # Weight towards hole 14
                
                # Invert weights so closer to middle has higher probability
                max_weight = max(weights)
                weights = [max_weight - w + 1 for w in weights]
                
                return random.choices(possible_holes, weights=weights)[0]
        
        # For delivery staff, can move anywhere
        else:
            # Occasionally return to clubhouse
            if random.random() < 0.2:
                return "clubhouse"
            
            # Otherwise move to a random hole, avoiding current location
            possible_holes = [h for h in range(1, 19) if h != current]
            return random.choice(possible_holes)
        
        # If no good option, stay in place
        return asset.current_location
    
    def simulate_asset_movement(self, asset: Union[BeverageCart, DeliveryStaff]) -> None:
        """
        Simulate asset movement based on their current state.
        This function updates the asset's location based on their state machine.
        """
        # Handle IDLE state - asset repositions for future orders
        if asset.status == AssetStatus.IDLE:
            # Only occasionally reposition (30% chance)
            if random.random() < 0.3:
                new_location = self.get_next_realistic_location(asset)
                asset.current_location = new_location
                print(f"{asset.name} (IDLE) repositioned to {new_location}")
        
        # Handle EN_ROUTE_TO_PICKUP - heading to clubhouse
        elif asset.status == AssetStatus.EN_ROUTE_TO_PICKUP:
            if asset.current_location != "clubhouse":
                new_location = self._move_towards_destination(
                    asset.current_location, "clubhouse"
                )
                asset.current_location = new_location
                print(f"{asset.name} moving towards clubhouse, now at {new_location}")
                
                # Check if arrived at pickup
                if new_location == "clubhouse":
                    asset.status = AssetStatus.WAITING_FOR_ORDER
                    print(f"{asset.name} arrived at clubhouse, waiting for order")
        
        # Handle WAITING_FOR_ORDER - stay at clubhouse
        elif asset.status == AssetStatus.WAITING_FOR_ORDER:
            # Simulate order becoming ready (50% chance)
            if random.random() < 0.5:
                # Get the order destination from current orders
                if asset.current_orders:
                    order = asset.current_orders[0]
                    asset.destination = order.hole_number
                    asset.status = AssetStatus.EN_ROUTE_TO_DROPOFF
                    print(f"{asset.name} picked up order, heading to hole {asset.destination}")
        
        # Handle EN_ROUTE_TO_DROPOFF - delivering to customer
        elif asset.status == AssetStatus.EN_ROUTE_TO_DROPOFF:
            if asset.destination and asset.current_location != asset.destination:
                new_location = self._move_towards_destination(
                    asset.current_location, asset.destination
                )
                asset.current_location = new_location
                print(f"{asset.name} delivering to hole {asset.destination}, now at {new_location}")
                
                # Check if arrived at destination
                if new_location == asset.destination:
                    # Complete delivery
                    if asset.current_orders:
                        order = asset.current_orders[0]
                        order.status = "delivered"
                        asset.current_orders.remove(order)
                        print(f"{asset.name} delivered order to hole {asset.destination}")
                    
                    # Reset to IDLE
                    asset.status = AssetStatus.IDLE
                    asset.destination = None
        
        # INACTIVE assets don't move
        elif asset.status == AssetStatus.INACTIVE:
            pass
    
    def update_asset_state_for_new_order(self, asset: Union[BeverageCart, DeliveryStaff], 
                                       order: Order) -> None:
        """
        Update asset state when a new order is assigned.
        This sets the appropriate state based on asset location.
        """
        asset.current_orders.append(order)
        
        # If already at clubhouse, wait for order
        if asset.current_location == "clubhouse":
            asset.status = AssetStatus.WAITING_FOR_ORDER
        else:
            # Need to go pick up the order first
            asset.status = AssetStatus.EN_ROUTE_TO_PICKUP
            
        print(f"{asset.name} assigned order {order.order_id}, status: {asset.status.value}")