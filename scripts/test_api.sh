#!/bin/bash
# Golf Course Delivery System - API Testing Script
# This script provides example curl commands to test the API manually

API_BASE="http://localhost:8000"

echo "================================"
echo "Golf Course Delivery API Testing"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to pretty print JSON
pretty_json() {
    python3 -m json.tool
}

# 1. Check API Health
echo -e "\n${BLUE}1. Checking API Health...${NC}"
curl -s "$API_BASE/" | pretty_json

# 2. Get all assets
echo -e "\n${BLUE}2. Getting all delivery assets...${NC}"
curl -s "$API_BASE/api/assets" | pretty_json

# 3. Create a new order at hole 5
echo -e "\n${BLUE}3. Creating order at hole 5...${NC}"
ORDER_RESPONSE=$(curl -s -X POST "$API_BASE/api/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "hole_number": 5,
    "items": ["Beer", "Hot Dog", "Chips"],
    "special_instructions": "Extra mustard on hot dog"
  }')
echo "$ORDER_RESPONSE" | pretty_json

# Extract order ID
ORDER_ID=$(echo "$ORDER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['order_id'])")
echo -e "${GREEN}Created order: $ORDER_ID${NC}"

# 4. Get order details
echo -e "\n${BLUE}4. Getting order details...${NC}"
curl -s "$API_BASE/api/orders/$ORDER_ID" | pretty_json

# 5. Dispatch the order
echo -e "\n${BLUE}5. Dispatching order...${NC}"
curl -s -X POST "$API_BASE/api/orders/$ORDER_ID/dispatch" | pretty_json

# 6. Update asset location (example: cart1 to hole 3)
echo -e "\n${BLUE}6. Updating asset location (cart1 to hole 3)...${NC}"
curl -s -X POST "$API_BASE/api/assets/cart1/location" \
  -H "Content-Type: application/json" \
  -d '{"location": 3}' | pretty_json

# 7. Create another order at hole 15 (back nine)
echo -e "\n${BLUE}7. Creating order at hole 15 (back nine)...${NC}"
ORDER2_RESPONSE=$(curl -s -X POST "$API_BASE/api/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "hole_number": 15,
    "items": ["Water", "Energy Bar"],
    "special_instructions": "Cold water please"
  }')
echo "$ORDER2_RESPONSE" | pretty_json

ORDER2_ID=$(echo "$ORDER2_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['order_id'])")

# 8. Dispatch second order
echo -e "\n${BLUE}8. Dispatching second order...${NC}"
curl -s -X POST "$API_BASE/api/orders/$ORDER2_ID/dispatch" | pretty_json

# 9. Get all orders
echo -e "\n${BLUE}9. Getting all orders...${NC}"
curl -s "$API_BASE/api/orders" | pretty_json

# 10. Update asset status
echo -e "\n${BLUE}10. Updating asset status (staff1 to available)...${NC}"
curl -s -X POST "$API_BASE/api/assets/staff1/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "available"}' | pretty_json

echo -e "\n${GREEN}Testing completed!${NC}"
echo "================================"

# Bonus: WebSocket test instructions
echo -e "\n${BLUE}To test WebSocket connection:${NC}"
echo "You can use wscat or any WebSocket client:"
echo "  npm install -g wscat"
echo "  wscat -c ws://localhost:8000/ws"
echo ""
echo "Or use the Python WebSocket client in scripts/ws_client.py"