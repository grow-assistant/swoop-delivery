"""
Configuration for Golf Course Delivery System Simulation
Adjust these settings to customize the randomization behavior
"""
import random

# Asset Starting Position Configurations
ASSET_START_CONFIG = {
    "cart1": {
        "name": "Reese",
        "type": "beverage_cart",
        "loop": "front_9",
        "start_locations": lambda: random.choice(list(range(1, 10))),  # Random hole 1-9
        "preferred_zones": list(range(1, 10))
    },
    "cart2": {
        "name": "Bev-Cart 2",
        "type": "beverage_cart", 
        "loop": "back_9",
        "start_locations": lambda: random.choice(list(range(10, 19))),  # Random hole 10-18
        "preferred_zones": list(range(10, 19))
    },
    "staff1": {
        "name": "Esteban",
        "type": "delivery_staff",
        "start_locations": lambda: random.choice(
            ["clubhouse", "clubhouse"] +  # Higher chance of starting at clubhouse
            list(range(1, 19))
        ),
        "preferred_zones": None  # Can go anywhere
    },
    "staff2": {
        "name": "Dylan",
        "type": "delivery_staff",
        "start_locations": lambda: random.choice(
            ["clubhouse"] + list(range(1, 19))  # Equal chance of any location
        ),
        "preferred_zones": None
    },
    "staff3": {
        "name": "Paige",
        "type": "delivery_staff",
        "start_locations": lambda: random.choice(list(range(1, 19))),  # Starts on course
        "preferred_zones": None
    }
}

# Movement Pattern Configurations
MOVEMENT_PATTERNS = {
    "beverage_cart": {
        "sequential_movement_chance": 0.8,  # 80% chance to move sequentially
        "return_to_start_chance": 0.05,     # 5% chance to return to loop start
        "skip_holes_chance": 0.15,          # 15% chance to skip holes
        "idle_time_range": (15, 30),        # Seconds to stay at each hole
        "movement_speed": "slow"            # Carts move slower
    },
    "delivery_staff": {
        "return_to_clubhouse_chance": 0.3,  # 30% chance to return to clubhouse
        "nearby_movement_chance": 0.5,      # 50% chance to move to nearby hole
        "long_jump_chance": 0.2,            # 20% chance to jump far
        "idle_time_range": (10, 20),        # Seconds to stay at each location
        "movement_speed": "fast"            # Staff move faster
    }
}

# Order Generation Configurations
ORDER_CONFIG = {
    "time_based_menu": {
        "morning": {
            "hours": (6, 10),
            "items": ["Coffee", "Breakfast Sandwich", "Energy Bar", "Orange Juice", "Water", "Banana"]
        },
        "midday": {
            "hours": (10, 14),
            "items": ["Beer", "Hot Dog", "Burger", "Soda", "Chips", "Water", "Nachos"]
        },
        "afternoon": {
            "hours": (14, 17),
            "items": ["Beer", "Energy Drink", "Snacks", "Ice Pack", "Water", "Pretzel"]
        },
        "evening": {
            "hours": (17, 22),
            "items": ["Beer", "Sandwich", "Chips", "Soda", "Water", "Wings"]
        }
    },
    "order_patterns": {
        "front_nine_weight": 0.6,           # 60% of orders on front nine
        "back_nine_weight": 0.4,            # 40% of orders on back nine
        "cluster_chance": 0.3,              # 30% chance of clustered orders
        "cluster_size_range": (2, 4),       # Groups of 2-4 players
        "items_per_order_range": (1, 3),    # 1-3 items per order
        "rush_hour_chance": 0.3             # 30% chance of rush hour conditions
    },
    "special_instructions": [
        "Player at hole {hole} tee box",
        "Deliver to hole {hole} green",
        "Group of {players} at hole {hole}",
        "Quick delivery needed at hole {hole}",
        "Call when arriving at hole {hole}",
        "Leave at hole {hole} cart path",
        "Meet at hole {hole} fairway",
        "Text on arrival to hole {hole}",
        ""  # No special instructions
    ]
}

# Simulation Timing Configurations
TIMING_CONFIG = {
    "simulation_duration": 300,              # 5 minutes default
    "order_interval_normal": (20, 40),       # Seconds between orders (normal)
    "order_interval_rush": (10, 20),         # Seconds between orders (rush)
    "dispatch_delay": (2, 5),                # Seconds before dispatching order
    "asset_movement_interval": {
        "beverage_cart": {
            "available": (15, 30),           # Movement interval when available
            "busy": (30, 45),                # Movement interval when busy
            "at_clubhouse": (20, 40)         # Longer wait at clubhouse
        },
        "delivery_staff": {
            "available": (10, 25),
            "busy": (25, 40),
            "at_clubhouse": (15, 30)
        }
    }
}

# Load Testing Configurations
LOAD_TEST_SCENARIOS = {
    "light": {
        "concurrent_assets": 2,
        "orders_per_simulation": (5, 8),
        "description": "Light load - quiet morning"
    },
    "normal": {
        "concurrent_assets": 3,
        "orders_per_simulation": (8, 12),
        "description": "Normal load - typical day"
    },
    "busy": {
        "concurrent_assets": 4,
        "orders_per_simulation": (12, 18),
        "description": "Busy load - weekend afternoon"
    },
    "stress": {
        "concurrent_assets": 5,
        "orders_per_simulation": (15, 25),
        "description": "Stress test - tournament day"
    }
}

# Randomization Helper Functions
def get_random_start_location(asset_id: str):
    """Get random starting location for an asset"""
    config = ASSET_START_CONFIG.get(asset_id, {})
    if "start_locations" in config:
        return config["start_locations"]()
    return "clubhouse"

def get_random_menu_items():
    """Get menu items based on time of day"""
    from datetime import datetime
    hour = datetime.now().hour
    
    for period, config in ORDER_CONFIG["time_based_menu"].items():
        start_hour, end_hour = config["hours"]
        if start_hour <= hour < end_hour:
            return config["items"]
    
    # Default to midday menu
    return ORDER_CONFIG["time_based_menu"]["midday"]["items"]

def get_random_special_instruction(hole_number: int):
    """Get random special instruction for an order"""
    instruction_template = random.choice(ORDER_CONFIG["special_instructions"])
    if instruction_template:
        return instruction_template.format(
            hole=hole_number,
            players=random.randint(2, 4)
        )
    return ""

def should_create_cluster():
    """Determine if orders should be clustered"""
    return random.random() < ORDER_CONFIG["order_patterns"]["cluster_chance"]

def get_cluster_size():
    """Get size of order cluster"""
    min_size, max_size = ORDER_CONFIG["order_patterns"]["cluster_size_range"]
    return random.randint(min_size, max_size)