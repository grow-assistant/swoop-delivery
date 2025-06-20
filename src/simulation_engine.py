"""
Enhanced simulation engine for the Swoop Delivery system.
Integrates configuration, metrics tracking, and event-driven simulation.
"""
import random
import heapq
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import uuid4

from .models import BeverageCart, DeliveryStaff, Order, AssetStatus, OrderStatus, DeliveryAsset
from .dispatcher import Dispatcher
from .simulation_config import SimulationConfig, DispatcherStrategy
from .simulation_summary import SimulationSummary
from .course_data import COURSE_DATA


class SimulationEvent:
    """Represents an event in the simulation."""
    def __init__(self, timestamp: datetime, event_type: str, data: Dict):
        self.timestamp = timestamp
        self.event_type = event_type
        self.data = data
    
    def __lt__(self, other):
        return self.timestamp < other.timestamp


class SimulationEngine:
    """Main simulation engine for running delivery scenarios."""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.summary = SimulationSummary(config=config)
        self.assets = []
        self.dispatcher = None
        self.event_queue = []
        self.current_time = datetime.now()
        self.end_time = datetime.now()  # Will be set properly in run()
        self.order_counter = 0
        self.pending_orders = []  # For batch processing
        
    def initialize_assets(self):
        """Initialize delivery assets based on configuration."""
        # Create beverage carts
        for i in range(self.config.num_beverage_carts):
            cart_id = f"cart{i+1}"
            loop = "front_9" if i % 2 == 0 else "back_9"
            start_location = random.choice(self.config.front_9_holes if loop == "front_9" 
                                         else self.config.back_9_holes)
            cart = BeverageCart(
                asset_id=cart_id,
                name=f"Bev-Cart {i+1}",
                loop=loop,
                current_location=start_location
            )
            self.assets.append(cart)
            self.summary.add_asset(cart)
        
        # Create delivery staff
        staff_names = ["Esteban", "Dylan", "Paige", "Alex", "Sam", "Jordan", "Casey", "Morgan"]
        for i in range(self.config.num_delivery_staff):
            staff_id = f"staff{i+1}"
            staff = DeliveryStaff(
                asset_id=staff_id,
                name=staff_names[i % len(staff_names)],
                current_location="clubhouse"
            )
            self.assets.append(staff)
            self.summary.add_asset(staff)
        
        # Initialize dispatcher with appropriate strategy
        self.dispatcher = Dispatcher(self.assets)
        self._configure_dispatcher_strategy()
        
        print(f"Initialized {len(self.assets)} delivery assets:")
        for asset in self.assets:
            asset_type = "Beverage Cart" if isinstance(asset, BeverageCart) else "Delivery Staff"
            location_info = f", Loop: {asset.loop}" if isinstance(asset, BeverageCart) else ""
            print(f"  - {asset.name} ({asset_type}) at location {asset.current_location}{location_info}")
    
    def _configure_dispatcher_strategy(self):
        """Configure the dispatcher based on the selected strategy."""
        # Update dispatcher parameters based on strategy
        if self.config.dispatcher_strategy == DispatcherStrategy.CART_PREFERENCE:
            self.dispatcher.BEV_CART_PREFERENCE_MIN = self.config.cart_preference_window_min
        
        # Set other dispatcher parameters from config
        self.dispatcher.PREP_TIME_MIN = self.config.prep_time_min
        self.dispatcher.TRAVEL_TIME_PER_HOLE = self.config.travel_time_per_hole
        self.dispatcher.PLAYER_MIN_PER_HOLE = self.config.player_min_per_hole
    
    def schedule_order_generation(self):
        """Schedule order generation events throughout the simulation."""
        current = self.current_time
        while current < self.end_time:
            # Add variance to order timing
            interval = random.gauss(
                self.config.order_generation_interval_min / self.config.order_volume_multiplier,
                self.config.order_generation_variance
            )
            interval = max(0.5, interval)  # Minimum 30 seconds between orders
            
            current += timedelta(minutes=interval)
            if current < self.end_time:
                hole = random.choice(self.config.front_9_holes + self.config.back_9_holes)
                event = SimulationEvent(
                    timestamp=current,
                    event_type="generate_order",
                    data={"hole_number": hole}
                )
                heapq.heappush(self.event_queue, event)
    
    def schedule_asset_updates(self):
        """Schedule periodic asset status updates."""
        interval = timedelta(minutes=1)  # Check asset status every minute
        current = self.current_time
        
        while current < self.end_time:
            current += interval
            if current < self.end_time:
                event = SimulationEvent(
                    timestamp=current,
                    event_type="update_assets",
                    data={}
                )
                heapq.heappush(self.event_queue, event)
    
    def run(self, duration_minutes: Optional[int] = None):
        """Run the simulation for the specified duration."""
        if duration_minutes is None:
            duration_minutes = self.config.simulation_duration_minutes
        
        self.current_time = datetime.now()
        self.end_time = self.current_time + timedelta(minutes=duration_minutes)
        
        print(f"\n{'='*60}")
        print(f"Starting Swoop Delivery Simulation")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Strategy: {self.config.dispatcher_strategy.value}")
        print(f"Order Volume Multiplier: {self.config.order_volume_multiplier}x")
        print(f"{'='*60}\n")
        
        # Initialize simulation
        self.initialize_assets()
        self.schedule_order_generation()
        self.schedule_asset_updates()
        
        # Add initial log event
        if self.config.enable_detailed_logging:
            self._schedule_log_event()
        
        # Main simulation loop
        while self.event_queue and self.current_time < self.end_time:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.timestamp
            
            if event.event_type == "generate_order":
                self._handle_order_generation(event)
            elif event.event_type == "update_assets":
                self._handle_asset_update(event)
            elif event.event_type == "complete_delivery":
                self._handle_delivery_completion(event)
            elif event.event_type == "process_batch":
                self._handle_batch_processing(event)
            elif event.event_type == "log_status":
                self._handle_log_status(event)
        
        # Finalize simulation
        self.summary.finalize(self.current_time)
        
        print(f"\nSimulation completed at {self.current_time.strftime('%H:%M:%S')}")
        
        # Print summary
        self.summary.print_summary()
        
        return self.summary
    
    def _handle_order_generation(self, event: SimulationEvent):
        """Handle order generation event."""
        self.order_counter += 1
        order = Order(
            order_id=f"ORD{self.order_counter:04d}",
            hole_number=event.data["hole_number"]
        )
        
        self.summary.add_order(order, self.current_time)
        
        if self.config.enable_detailed_logging:
            print(f"[{self._format_time()}] New order {order.order_id} for hole {order.hole_number}")
        
        # Handle based on strategy
        if self.config.dispatcher_strategy == DispatcherStrategy.BATCH_ORDERS:
            self.pending_orders.append((order, self.current_time))
            # Schedule batch processing if not already scheduled
            if len(self.pending_orders) == 1:  # First order in batch
                batch_time = self.current_time + timedelta(minutes=self.config.batch_time_window_min)
                event = SimulationEvent(
                    timestamp=batch_time,
                    event_type="process_batch",
                    data={}
                )
                heapq.heappush(self.event_queue, event)
        else:
            self._dispatch_single_order(order)
    
    def _handle_batch_processing(self, event: SimulationEvent):
        """Process batched orders."""
        if not self.pending_orders:
            return
        
        # Group orders by proximity
        batches = self._group_orders_for_batching()
        
        for batch in batches:
            if len(batch) > 1:
                # Record batch in summary
                order_ids = [order.order_id for order, _ in batch]
                self.summary.record_batch(order_ids, len(batch))
                
                if self.config.enable_detailed_logging:
                    print(f"[{self._format_time()}] Batching {len(batch)} orders: {', '.join(order_ids)}")
            
            # Dispatch each order in the batch
            for order, order_time in batch:
                self._dispatch_single_order(order)
        
        self.pending_orders.clear()
    
    def _group_orders_for_batching(self) -> List[List[Tuple[Order, datetime]]]:
        """Group orders for efficient batching."""
        if len(self.pending_orders) <= 1:
            return [self.pending_orders]
        
        # Simple proximity-based grouping
        batches = []
        processed = set()
        
        for i, (order1, time1) in enumerate(self.pending_orders):
            if i in processed:
                continue
            
            batch = [(order1, time1)]
            processed.add(i)
            
            # Find nearby orders
            for j, (order2, time2) in enumerate(self.pending_orders):
                if j in processed:
                    continue
                
                # Check if orders are close enough to batch
                hole_distance = abs(order1.hole_number - order2.hole_number)
                if hole_distance <= 2 and len(batch) < self.config.max_orders_per_batch:
                    batch.append((order2, time2))
                    processed.add(j)
            
            batches.append(batch)
        
        return batches
    
    def _dispatch_single_order(self, order: Order):
        """Dispatch a single order."""
        # Use appropriate strategy
        if self.config.dispatcher_strategy == DispatcherStrategy.ZONE_OPTIMAL:
            best_asset = self._find_zone_optimal_asset(order)
        else:
            if self.dispatcher:
                best_candidate = self.dispatcher.find_best_candidate(order)
                best_asset = best_candidate["asset"] if best_candidate else None
            else:
                best_asset = None
        
        if best_asset and self.dispatcher:
            # Calculate delivery details
            eta, predicted_hole = self.dispatcher.calculate_eta_and_destination(
                best_asset, order.hole_number
            )
            
            # Update order and asset
            order.assigned_to = best_asset
            order.status = OrderStatus.ASSIGNED
            best_asset.status = AssetStatus.ON_DELIVERY
            best_asset.current_orders.append(order)
            
            # Record in summary
            self.summary.record_assignment(
                order.order_id, best_asset, self.current_time, predicted_hole
            )
            
            # Schedule delivery completion
            delivery_time = self.current_time + timedelta(minutes=eta)
            event = SimulationEvent(
                timestamp=delivery_time,
                event_type="complete_delivery",
                data={
                    "order_id": order.order_id,
                    "asset_id": best_asset.asset_id,
                    "delivery_hole": predicted_hole
                }
            )
            heapq.heappush(self.event_queue, event)
            
            if self.config.enable_detailed_logging:
                print(f"[{self._format_time()}] Order {order.order_id} assigned to {best_asset.name}, "
                      f"ETA: {eta:.1f} min at hole {predicted_hole}")
        else:
            print(f"[{self._format_time()}] WARNING: No available asset for order {order.order_id}")
    
    def _find_zone_optimal_asset(self, order: Order) -> Optional[DeliveryAsset]:
        """Find the best asset prioritizing zone optimization."""
        available_assets = [a for a in self.assets if a.status == AssetStatus.AVAILABLE]
        
        if not available_assets:
            return None
        
        # Prioritize assets already in the same zone
        order_on_front = order.hole_number in self.config.front_9_holes
        
        zone_assets = []
        other_assets = []
        
        for asset in available_assets:
            if isinstance(asset, BeverageCart):
                if (order_on_front and asset.loop == "front_9") or \
                   (not order_on_front and asset.loop == "back_9"):
                    zone_assets.append(asset)
            else:
                # Staff can go anywhere but check current location
                staff_on_front = asset.current_location in self.config.front_9_holes
                if (order_on_front and staff_on_front) or \
                   (not order_on_front and not staff_on_front):
                    zone_assets.append(asset)
                else:
                    other_assets.append(asset)
        
        # Choose from zone assets first
        candidates = zone_assets if zone_assets else other_assets
        
        if candidates:
            # Find closest asset
            best_asset = None
            best_eta = float('inf')
            
            for asset in candidates:
                eta, _ = self.dispatcher.calculate_eta_and_destination(asset, order.hole_number)
                if eta < best_eta:
                    best_eta = eta
                    best_asset = asset
            
            return best_asset
        
        return None
    
    def _handle_delivery_completion(self, event: SimulationEvent):
        """Handle delivery completion event."""
        order_id = event.data["order_id"]
        asset_id = event.data["asset_id"]
        delivery_hole = event.data["delivery_hole"]
        
        # Find asset and order
        asset = next((a for a in self.assets if a.asset_id == asset_id), None)
        if not asset:
            return
        
        order = next((o for o in asset.current_orders if o.order_id == order_id), None)
        if not order:
            return
        
        # Update order status
        order.status = OrderStatus.DELIVERED
        asset.current_orders.remove(order)
        
        # Update asset location
        old_location = asset.current_location
        asset.current_location = delivery_hole
        
        # Calculate distance traveled
        distance = abs(self._get_hole_number(delivery_hole) - self._get_hole_number(old_location))
        distance += abs(self._get_hole_number(old_location) - 0)  # To clubhouse
        distance += abs(self._get_hole_number(delivery_hole) - 0)  # From clubhouse
        self.summary.update_asset_distance(asset_id, distance)
        
        # Update asset status if no more orders
        if not asset.current_orders:
            asset.status = AssetStatus.AVAILABLE
        
        # Record delivery in summary
        self.summary.record_delivery(order_id, self.current_time, delivery_hole)
        
        if self.config.enable_detailed_logging:
            print(f"[{self._format_time()}] Order {order_id} delivered by {asset.name} at hole {delivery_hole}")
    
    def _handle_asset_update(self, event: SimulationEvent):
        """Update asset utilization metrics."""
        for asset in self.assets:
            is_active = asset.status == AssetStatus.ON_DELIVERY
            self.summary.update_asset_status(asset.asset_id, is_active, 1.0)  # 1 minute update
    
    def _handle_log_status(self, event: SimulationEvent):
        """Log intermediate status."""
        print(f"\n[{self._format_time()}] Status Update:")
        
        # Asset status
        active_assets = sum(1 for a in self.assets if a.status == AssetStatus.ON_DELIVERY)
        print(f"  Active Assets: {active_assets}/{len(self.assets)}")
        
        # Order stats
        total_orders = len(self.summary.orders)
        completed_orders = sum(1 for o in self.summary.orders.values() if o.delivery_time)
        pending_orders = total_orders - completed_orders
        
        print(f"  Orders: {completed_orders} completed, {pending_orders} pending")
        
        # Calculate current metrics
        if completed_orders > 0:
            recent_deliveries = [
                o.delivery_time_minutes for o in self.summary.orders.values()
                if o.delivery_time and o.delivery_time_minutes
            ][-10:]  # Last 10 deliveries
            
            if recent_deliveries:
                avg_recent = sum(recent_deliveries) / len(recent_deliveries)
                print(f"  Recent Avg Delivery Time: {avg_recent:.1f} minutes")
        
        # Schedule next log
        self._schedule_log_event()
    
    def _schedule_log_event(self):
        """Schedule the next status log event."""
        next_log_time = self.current_time + timedelta(minutes=self.config.log_interval_minutes)
        if next_log_time < self.end_time:
            event = SimulationEvent(
                timestamp=next_log_time,
                event_type="log_status",
                data={}
            )
            heapq.heappush(self.event_queue, event)
    
    def _get_hole_number(self, location) -> int:
        """Convert location to hole number."""
        if isinstance(location, str) and location.lower() == "clubhouse":
            return 0
        return int(location)
    
    def _format_time(self) -> str:
        """Format current time for logging."""
        elapsed = (self.current_time - self.summary.simulation_start_time).total_seconds() / 60
        return f"{elapsed:6.1f}min"