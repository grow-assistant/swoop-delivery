"""
Contains the course layout and data for Pinetree Country Club.
"""

# The zones for each beverage cart. While ETA is calculated per hole,
# carts are still restricted to their designated nines.
FRONT_NINE_HOLES = range(1, 10) # Holes 1-9
BACK_NINE_HOLES = range(10, 19) # Holes 10-18

COURSE_DATA = {
    "name": "Pinetree Country Club",
    "holes": 18,
    "front_9_holes": FRONT_NINE_HOLES,
    "back_9_holes": BACK_NINE_HOLES,
} 