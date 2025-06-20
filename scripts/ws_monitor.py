#!/usr/bin/env python3
"""
WebSocket Monitor for Golf Course Delivery System
Connects to the WebSocket endpoint and displays real-time updates
"""
import asyncio
import json
import signal
import sys
from datetime import datetime
from typing import Dict, Any

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    USE_RICH = True
except ImportError:
    print("For better visualization, install rich: pip install rich")
    USE_RICH = False

# Configuration
WS_URL = "ws://localhost:8000/ws"

class WebSocketMonitor:
    """Monitor WebSocket events from the Golf Course Delivery System"""
    
    def __init__(self):
        self.console = Console() if USE_RICH else None
        self.events = []
        self.orders = {}
        self.assets = {}
        self.running = True
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if USE_RICH and self.console:
            color_map = {
                "INFO": "blue",
                "SUCCESS": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "WS": "cyan"
            }
            color = color_map.get(level, "white")
            self.console.print(f"[{timestamp}] [{color}]{level}[/{color}] {message}")
        else:
            print(f"[{timestamp}] [{level}] {message}")
    
    def handle_event(self, data: Dict[str, Any]):
        """Handle incoming WebSocket event"""
        event_type = data.get("type", "unknown")
        timestamp = data.get("timestamp", datetime.now().isoformat())
        
        self.events.append({
            "time": timestamp,
            "type": event_type,
            "data": data
        })
        
        # Handle specific event types
        if event_type == "new_order":
            order = data.get("order", {})
            self.orders[order.get("order_id")] = order
            self.log(f"New order {order.get('order_id')} at hole {order.get('hole_number')}", "SUCCESS")
            
        elif event_type == "order_dispatched":
            dispatch = data.get("dispatch", {})
            order_id = dispatch.get("order_id")
            if order_id in self.orders:
                self.orders[order_id]["status"] = "dispatched"
                self.orders[order_id]["asset"] = dispatch.get("asset_name")
            self.log(
                f"Order {order_id} dispatched to {dispatch.get('asset_name')} "
                f"(ETA: {dispatch.get('eta_minutes', 0):.1f} min)", 
                "SUCCESS"
            )
            
        elif event_type == "location_update":
            asset_id = data.get("asset_id")
            location = data.get("location")
            if asset_id:
                if asset_id not in self.assets:
                    self.assets[asset_id] = {}
                self.assets[asset_id]["location"] = location
            self.log(f"Asset {asset_id} moved to {location}", "INFO")
            
        elif event_type == "status_update":
            asset_id = data.get("asset_id")
            status = data.get("status")
            if asset_id:
                if asset_id not in self.assets:
                    self.assets[asset_id] = {}
                self.assets[asset_id]["status"] = status
            self.log(f"Asset {asset_id} status changed to {status}", "INFO")
            
        elif event_type == "order_completed":
            order_id = data.get("order_id")
            if order_id in self.orders:
                self.orders[order_id]["status"] = "completed"
            self.log(f"Order {order_id} completed", "SUCCESS")
    
    def display_dashboard(self):
        """Display a live dashboard (if rich is installed)"""
        if not USE_RICH or not self.console:
            return
            
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Header
        header = Panel(
            "[bold blue]Golf Course Delivery System Monitor[/bold blue]\n"
            "Real-time WebSocket Event Monitoring",
            style="blue"
        )
        layout["header"].update(header)
        
        # Main content - Recent events
        events_table = Table(title="Recent Events", show_header=True)
        events_table.add_column("Time", style="cyan")
        events_table.add_column("Type", style="green")
        events_table.add_column("Details", style="white")
        
        # Show last 10 events
        for event in self.events[-10:]:
            time_str = datetime.fromisoformat(event["time"]).strftime("%H:%M:%S")
            events_table.add_row(
                time_str,
                event["type"],
                str(event["data"])[:50] + "..."
            )
        
        layout["main"].update(events_table)
        
        # Footer
        footer = Panel(
            f"Connected to: {WS_URL} | Events: {len(self.events)} | "
            f"Orders: {len(self.orders)} | Press Ctrl+C to exit",
            style="dim"
        )
        layout["footer"].update(footer)
        
        return layout
    
    async def connect_and_monitor(self):
        """Connect to WebSocket and monitor events"""
        self.log(f"Connecting to {WS_URL}...", "INFO")
        
        try:
            async with websockets.connect(WS_URL) as websocket:
                self.log("Connected successfully!", "SUCCESS")
                
                # Handle incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        self.handle_event(data)
                    except json.JSONDecodeError:
                        self.log(f"Invalid JSON received: {message}", "ERROR")
                    except Exception as e:
                        self.log(f"Error handling message: {e}", "ERROR")
                        
        except websockets.exceptions.WebSocketException as e:
            self.log(f"WebSocket error: {e}", "ERROR")
        except Exception as e:
            self.log(f"Connection error: {e}", "ERROR")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log("\nShutting down...", "INFO")
        self.running = False
        sys.exit(0)
    
    async def run(self):
        """Run the monitor"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start monitoring
        await self.connect_and_monitor()


async def main():
    """Main entry point"""
    monitor = WebSocketMonitor()
    
    print("""
    ╔════════════════════════════════════════════╗
    ║     Golf Course Delivery WebSocket Monitor  ║
    ║                                            ║
    ║   Monitoring real-time events:             ║
    ║   - New orders                             ║
    ║   - Order dispatches                       ║
    ║   - Asset location updates                 ║
    ║   - Status changes                         ║
    ║   - Order completions                      ║
    ╚════════════════════════════════════════════╝
    """)
    
    await monitor.run()


if __name__ == "__main__":
    asyncio.run(main())