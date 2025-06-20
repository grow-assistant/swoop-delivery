"""
Simulation summary and metrics collection for the Swoop Delivery system.
Tracks key performance indicators throughout the simulation.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from statistics import mean, median, stdev
from .models import Order, DeliveryAsset, BeverageCart, DeliveryStaff, OrderStatus

@dataclass
class OrderMetrics:
    """Metrics for a single order."""
    order_id: str
    order_time: datetime
    hole_number: int
    assigned_asset: Optional[str] = None
    assignment_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    predicted_delivery_hole: Optional[int] = None
    actual_delivery_hole: Optional[int] = None
    was_batched: bool = False
    batch_size: int = 1

    @property
    def wait_time_minutes(self) -> Optional[float]:
        """Time from order placement to assignment."""
        if self.assignment_time:
            return (self.assignment_time - self.order_time).total_seconds() / 60
        return None

    @property
    def delivery_time_minutes(self) -> Optional[float]:
        """Total time from order placement to delivery."""
        if self.delivery_time:
            return (self.delivery_time - self.order_time).total_seconds() / 60
        return None

    @property
    def preparation_delivery_time_minutes(self) -> Optional[float]:
        """Time from assignment to delivery."""
        if self.assignment_time and self.delivery_time:
            return (self.delivery_time - self.assignment_time).total_seconds() / 60
        return None

@dataclass
class AssetMetrics:
    """Metrics for a single delivery asset."""
    asset_id: str
    asset_name: str
    asset_type: str  # "beverage_cart" or "delivery_staff"
    total_orders_delivered: int = 0
    total_delivery_time_minutes: float = 0.0
    total_distance_traveled: float = 0.0  # in holes
    idle_time_minutes: float = 0.0
    active_time_minutes: float = 0.0
    orders_history: List[str] = field(default_factory=list)

    @property
    def utilization_rate(self) -> float:
        """Percentage of time asset was active."""
        total_time = self.idle_time_minutes + self.active_time_minutes
        if total_time > 0:
            return (self.active_time_minutes / total_time) * 100
        return 0.0

    @property
    def avg_delivery_time_minutes(self) -> float:
        """Average delivery time per order."""
        if self.total_orders_delivered > 0:
            return self.total_delivery_time_minutes / self.total_orders_delivered
        return 0.0

@dataclass
class SimulationSummary:
    """Collects and analyzes simulation metrics."""
    simulation_start_time: datetime = field(default_factory=datetime.now)
    simulation_end_time: Optional[datetime] = None
    
    # Order tracking
    orders: Dict[str, OrderMetrics] = field(default_factory=dict)
    
    # Asset tracking
    assets: Dict[str, AssetMetrics] = field(default_factory=dict)
    
    # Event log
    events: List[Dict] = field(default_factory=list)
    
    # Configuration reference
    config: Optional[object] = None

    def add_order(self, order: Order, timestamp: datetime):
        """Record a new order."""
        self.orders[order.order_id] = OrderMetrics(
            order_id=order.order_id,
            order_time=timestamp,
            hole_number=order.hole_number
        )
        self.log_event("order_placed", {
            "order_id": order.order_id,
            "hole_number": order.hole_number,
            "timestamp": timestamp
        })

    def record_assignment(self, order_id: str, asset: DeliveryAsset, 
                         timestamp: datetime, predicted_hole: int):
        """Record order assignment to an asset."""
        if order_id in self.orders:
            self.orders[order_id].assigned_asset = asset.asset_id
            self.orders[order_id].assignment_time = timestamp
            self.orders[order_id].predicted_delivery_hole = predicted_hole
            
            # Update asset metrics
            if asset.asset_id in self.assets:
                self.assets[asset.asset_id].orders_history.append(order_id)
            
            self.log_event("order_assigned", {
                "order_id": order_id,
                "asset_id": asset.asset_id,
                "asset_name": asset.name,
                "predicted_hole": predicted_hole,
                "timestamp": timestamp
            })

    def record_delivery(self, order_id: str, timestamp: datetime, 
                       actual_hole: int):
        """Record order delivery completion."""
        if order_id in self.orders:
            order_metrics = self.orders[order_id]
            order_metrics.delivery_time = timestamp
            order_metrics.actual_delivery_hole = actual_hole
            
            # Update asset metrics
            if order_metrics.assigned_asset in self.assets:
                asset = self.assets[order_metrics.assigned_asset]
                asset.total_orders_delivered += 1
                if order_metrics.delivery_time_minutes:
                    asset.total_delivery_time_minutes += order_metrics.delivery_time_minutes
            
            self.log_event("order_delivered", {
                "order_id": order_id,
                "actual_hole": actual_hole,
                "delivery_time_minutes": order_metrics.delivery_time_minutes,
                "timestamp": timestamp
            })

    def record_batch(self, order_ids: List[str], batch_size: int):
        """Record that orders were batched together."""
        for order_id in order_ids:
            if order_id in self.orders:
                self.orders[order_id].was_batched = True
                self.orders[order_id].batch_size = batch_size

    def add_asset(self, asset: DeliveryAsset):
        """Register an asset for tracking."""
        asset_type = "beverage_cart" if isinstance(asset, BeverageCart) else "delivery_staff"
        self.assets[asset.asset_id] = AssetMetrics(
            asset_id=asset.asset_id,
            asset_name=asset.name,
            asset_type=asset_type
        )

    def update_asset_status(self, asset_id: str, is_active: bool, 
                           duration_minutes: float):
        """Update asset active/idle time."""
        if asset_id in self.assets:
            if is_active:
                self.assets[asset_id].active_time_minutes += duration_minutes
            else:
                self.assets[asset_id].idle_time_minutes += duration_minutes

    def update_asset_distance(self, asset_id: str, distance_holes: float):
        """Update distance traveled by asset."""
        if asset_id in self.assets:
            self.assets[asset_id].total_distance_traveled += distance_holes

    def log_event(self, event_type: str, details: Dict):
        """Log a simulation event."""
        self.events.append({
            "type": event_type,
            "details": details,
            "timestamp": details.get("timestamp", datetime.now())
        })

    def finalize(self, end_time: datetime):
        """Finalize the simulation and prepare summary."""
        self.simulation_end_time = end_time

    def calculate_kpis(self) -> Dict[str, Any]:
        """Calculate key performance indicators."""
        # Order metrics
        completed_orders = [o for o in self.orders.values() if o.delivery_time]
        
        if not completed_orders:
            return {"error": "No completed orders to analyze"}
        
        # Efficiency Metrics
        delivery_times = [o.delivery_time_minutes for o in completed_orders 
                         if o.delivery_time_minutes is not None]
        wait_times = [o.wait_time_minutes for o in completed_orders 
                     if o.wait_time_minutes is not None]
        
        # Asset utilization
        asset_utilizations = [a.utilization_rate for a in self.assets.values()]
        
        # Calculate simulation duration
        if self.simulation_end_time:
            total_hours = (self.simulation_end_time - self.simulation_start_time).total_seconds() / 3600
        else:
            total_hours = 0
        
        # Orders per hour
        orders_per_hour = len(completed_orders) / total_hours if total_hours > 0 else 0
        
        # Batching metrics
        batched_orders = [o for o in completed_orders if o.was_batched]
        batch_percentage = (len(batched_orders) / len(completed_orders) * 100) if completed_orders else 0
        
        # Asset-specific metrics
        cart_metrics = [a for a in self.assets.values() if a.asset_type == "beverage_cart"]
        staff_metrics = [a for a in self.assets.values() if a.asset_type == "delivery_staff"]
        
        kpis = {
            # Efficiency Metrics
            "avg_delivery_time_min": mean(delivery_times) if delivery_times else 0,
            "median_delivery_time_min": median(delivery_times) if delivery_times else 0,
            "min_delivery_time_min": min(delivery_times) if delivery_times else 0,
            "max_delivery_time_min": max(delivery_times) if delivery_times else 0,
            "delivery_time_std_dev": stdev(delivery_times) if len(delivery_times) > 1 else 0,
            
            "avg_asset_utilization_pct": mean(asset_utilizations) if asset_utilizations else 0,
            "orders_delivered_per_hour": orders_per_hour,
            "total_orders_delivered": len(completed_orders),
            
            # Quality Metrics
            "avg_customer_wait_time_min": mean(wait_times) if wait_times else 0,
            "median_customer_wait_time_min": median(wait_times) if wait_times else 0,
            "percentage_orders_batched": batch_percentage,
            
            # Asset breakdown
            "beverage_cart_utilization_pct": mean([a.utilization_rate for a in cart_metrics]) if cart_metrics else 0,
            "delivery_staff_utilization_pct": mean([a.utilization_rate for a in staff_metrics]) if staff_metrics else 0,
            "beverage_cart_orders": sum(a.total_orders_delivered for a in cart_metrics),
            "delivery_staff_orders": sum(a.total_orders_delivered for a in staff_metrics),
            
            # Simulation info
            "simulation_duration_hours": total_hours,
            "total_assets": len(self.assets),
            "total_events": len(self.events)
        }
        
        # Add target achievement metrics if config is available
        if self.config:
            target_delivery = getattr(self.config, 'target_delivery_time_min', 25)
            target_wait = getattr(self.config, 'target_wait_time_min', 20)
            
            on_time_deliveries = [o for o in completed_orders 
                                 if o.delivery_time_minutes and o.delivery_time_minutes <= target_delivery]
            on_time_waits = [o for o in completed_orders 
                           if o.wait_time_minutes and o.wait_time_minutes <= target_wait]
            
            kpis["on_time_delivery_pct"] = (len(on_time_deliveries) / len(completed_orders) * 100) if completed_orders else 0
            kpis["on_time_wait_pct"] = (len(on_time_waits) / len(completed_orders) * 100) if completed_orders else 0
        
        return kpis

    def print_summary(self):
        """Print a formatted summary of the simulation."""
        kpis = self.calculate_kpis()
        
        print("\n" + "="*60)
        print("SIMULATION SUMMARY")
        print("="*60)
        
        if "error" in kpis:
            print(f"Error: {kpis['error']}")
            return
        
        print(f"\n📊 SIMULATION OVERVIEW")
        print(f"Duration: {kpis['simulation_duration_hours']:.2f} hours")
        print(f"Total Orders Delivered: {kpis['total_orders_delivered']}")
        print(f"Total Events: {kpis['total_events']}")
        
        print(f"\n⚡ EFFICIENCY METRICS")
        print(f"Average Delivery Time: {kpis['avg_delivery_time_min']:.1f} minutes")
        print(f"Median Delivery Time: {kpis['median_delivery_time_min']:.1f} minutes")
        print(f"Delivery Time Range: {kpis['min_delivery_time_min']:.1f} - {kpis['max_delivery_time_min']:.1f} minutes")
        print(f"Standard Deviation: {kpis['delivery_time_std_dev']:.1f} minutes")
        print(f"Orders Delivered per Hour: {kpis['orders_delivered_per_hour']:.1f}")
        
        print(f"\n📦 ASSET UTILIZATION")
        print(f"Average Asset Utilization: {kpis['avg_asset_utilization_pct']:.1f}%")
        print(f"Beverage Cart Utilization: {kpis['beverage_cart_utilization_pct']:.1f}%")
        print(f"Delivery Staff Utilization: {kpis['delivery_staff_utilization_pct']:.1f}%")
        print(f"Orders by Beverage Carts: {kpis['beverage_cart_orders']}")
        print(f"Orders by Delivery Staff: {kpis['delivery_staff_orders']}")
        
        print(f"\n🎯 QUALITY METRICS")
        print(f"Average Customer Wait Time: {kpis['avg_customer_wait_time_min']:.1f} minutes")
        print(f"Median Customer Wait Time: {kpis['median_customer_wait_time_min']:.1f} minutes")
        print(f"Percentage of Orders Batched: {kpis['percentage_orders_batched']:.1f}%")
        
        if "on_time_delivery_pct" in kpis:
            print(f"\n✅ TARGET ACHIEVEMENT")
            print(f"On-Time Delivery Rate: {kpis['on_time_delivery_pct']:.1f}%")
            print(f"On-Time Wait Rate: {kpis['on_time_wait_pct']:.1f}%")
        
        print("\n" + "="*60)
        
        # Print asset-specific details
        print("\n📋 ASSET PERFORMANCE DETAILS")
        print("-"*60)
        for asset in self.assets.values():
            print(f"\n{asset.asset_name} ({asset.asset_type.replace('_', ' ').title()})")
            print(f"  Orders Delivered: {asset.total_orders_delivered}")
            print(f"  Utilization Rate: {asset.utilization_rate:.1f}%")
            print(f"  Avg Delivery Time: {asset.avg_delivery_time_minutes:.1f} minutes")
            print(f"  Distance Traveled: {asset.total_distance_traveled:.1f} holes")

    def export_detailed_report(self) -> Dict:
        """Export detailed report for further analysis."""
        return {
            "kpis": self.calculate_kpis(),
            "orders": {oid: {
                "order_id": o.order_id,
                "hole_number": o.hole_number,
                "wait_time_min": o.wait_time_minutes,
                "delivery_time_min": o.delivery_time_minutes,
                "was_batched": o.was_batched,
                "assigned_asset": o.assigned_asset
            } for oid, o in self.orders.items()},
            "assets": {aid: {
                "asset_id": a.asset_id,
                "asset_name": a.asset_name,
                "asset_type": a.asset_type,
                "utilization_rate": a.utilization_rate,
                "total_orders": a.total_orders_delivered,
                "avg_delivery_time": a.avg_delivery_time_minutes
            } for aid, a in self.assets.items()},
            "events": self.events[:100]  # First 100 events to avoid huge export
        }