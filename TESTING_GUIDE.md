# Golf Course Delivery System - Testing Guide

This guide provides comprehensive instructions for testing the Golf Course Delivery System with dummy locations and simulated scenarios.

## Quick Start

### 1. Start the System

```bash
# Using Docker Compose (recommended)
make docker-up

# Or run locally
make db-setup
make redis-setup
make run
```

### 2. Verify System Health

```bash
# Check API health
curl http://localhost:8000/

# Check available assets
curl http://localhost:8000/api/assets
```

## Testing Tools Overview

We provide several testing tools in the `scripts/` directory:

1. **test_api.sh** - Manual API testing with curl commands
2. **test_simulation.py** - Automated simulation of orders and asset movements
3. **ws_monitor.py** - Real-time WebSocket monitoring
4. **load_test.py** - Performance and load testing

## Manual Testing

### Using the Shell Script

```bash
# Make the script executable
chmod +x scripts/test_api.sh

# Run the test script
./scripts/test_api.sh
```

This script will:
- Create orders at different holes
- Dispatch orders to available assets
- Update asset locations
- Show order status

### Using curl Commands

```bash
# Create an order at hole 7
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "hole_number": 7,
    "items": ["Beer", "Hot Dog"],
    "special_instructions": "No onions"
  }'

# Dispatch the order (replace ORDER_ID)
curl -X POST http://localhost:8000/api/orders/ORD0001/dispatch

# Update asset location
curl -X POST http://localhost:8000/api/assets/cart1/location \
  -H "Content-Type: application/json" \
  -d '{"location": 5}'
```

## Automated Simulation

### Running the Full Simulation

```bash
# Install dependencies
pip install requests websockets aiohttp

# Run the simulation
python scripts/test_simulation.py
```

The simulation will:
- Create random orders at different holes (1-18)
- Move assets around the course
- Dispatch orders automatically
- Monitor WebSocket events
- Run for 5 minutes by default

### Simulation Features

1. **Realistic Movement Patterns**
   - Beverage carts stay in their assigned loops (front 9 or back 9)
   - Delivery staff can move anywhere on the course
   - Assets move every 10-20 seconds

2. **Order Generation**
   - Random holes (1-18)
   - Random menu items
   - Automatic dispatching after creation

3. **Real-time Monitoring**
   - WebSocket connection for live updates
   - Console logging of all events

## WebSocket Monitoring

Monitor real-time events in a separate terminal:

```bash
# Basic monitoring
python scripts/ws_monitor.py

# With rich formatting (install rich first)
pip install rich
python scripts/ws_monitor.py
```

Events monitored:
- New orders
- Order dispatches
- Asset location updates
- Status changes
- Order completions

## Load Testing

### Running Load Tests

```bash
# Normal load (10 concurrent users)
python scripts/load_test.py --scenario normal

# Peak hours (50 concurrent users)
python scripts/load_test.py --scenario peak

# Stress test (100 concurrent users)
python scripts/load_test.py --scenario stress
```

### Load Test Scenarios

1. **Normal Load**
   - 10 concurrent users
   - 5 orders per user
   - 5-15 seconds between orders

2. **Peak Hours**
   - 50 concurrent users
   - 3 orders per user
   - 2-8 seconds between orders

3. **Stress Test**
   - 100 concurrent users
   - 2 orders per user
   - 1-3 seconds between orders

### Metrics Collected

- Total orders created/dispatched
- Response time statistics (avg, min, max, p95)
- Throughput (orders/second)
- Success rate
- Error tracking

## Testing Scenarios

### Scenario 1: Front Nine Rush

Test heavy load on the front nine:

```python
# Create multiple orders on holes 1-9
for hole in range(1, 10):
    curl -X POST http://localhost:8000/api/orders \
      -H "Content-Type: application/json" \
      -d "{\"hole_number\": $hole}"
```

### Scenario 2: Cart Zone Restriction

Verify carts stay in their zones:

```bash
# Order on hole 5 (front nine) - should go to cart1 or staff
curl -X POST http://localhost:8000/api/orders \
  -d '{"hole_number": 5}'

# Order on hole 15 (back nine) - should go to cart2 or staff
curl -X POST http://localhost:8000/api/orders \
  -d '{"hole_number": 15}'
```

### Scenario 3: Asset Availability

Test when all assets are busy:

```bash
# Set all assets to busy
curl -X POST http://localhost:8000/api/assets/cart1/status \
  -d '{"status": "on_delivery"}'
curl -X POST http://localhost:8000/api/assets/cart2/status \
  -d '{"status": "on_delivery"}'
curl -X POST http://localhost:8000/api/assets/staff1/status \
  -d '{"status": "on_delivery"}'

# Try to create and dispatch an order
curl -X POST http://localhost:8000/api/orders \
  -d '{"hole_number": 10}'
```

## Dummy Location Reference

### Golf Course Layout

```
Front Nine (Holes 1-9):
- Hole 1: Starting tee
- Holes 2-8: Various locations
- Hole 9: Turn to back nine

Back Nine (Holes 10-18):
- Hole 10: Start of back nine
- Holes 11-17: Various locations
- Hole 18: Final hole

Clubhouse: Central location (starting point)
```

### Asset Starting Positions

- **cart1 (Reese)**: Front 9, starts at hole 1
- **cart2 (Bev-Cart 2)**: Back 9, starts at hole 10
- **staff1 (Esteban)**: Clubhouse
- **staff2 (Dylan)**: Hole 18
- **staff3 (Paige)**: Hole 5

## Monitoring Performance

### Using Prometheus Metrics

Access metrics at: http://localhost:8000/metrics

Key metrics:
- Request count and latency
- Order processing times
- Asset utilization
- System health

### Using Grafana Dashboards

Access Grafana at: http://localhost:3000 (admin/admin)

Import dashboards for:
- System overview
- Order processing
- Asset performance
- API performance

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Ensure services are running
   docker-compose ps
   # Check logs
   docker-compose logs app
   ```

2. **No Available Assets**
   ```bash
   # Reset asset status
   curl -X POST http://localhost:8000/api/assets/cart1/status \
     -d '{"status": "available"}'
   ```

3. **WebSocket Connection Failed**
   ```bash
   # Check if WebSocket endpoint is accessible
   curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     http://localhost:8000/ws
   ```

## Advanced Testing

### Custom Scenarios

Create your own test scenarios by modifying the simulation script:

```python
# Example: Test specific route optimization
async def test_route_optimization(simulator):
    # Create orders at strategic locations
    orders = []
    for hole in [3, 5, 7]:  # Clustered orders
        order = simulator.create_order(hole)
        orders.append(order)
    
    # Dispatch all at once
    for order in orders:
        simulator.dispatch_order(order['order_id'])
```

### Integration Testing

Test with external systems:
1. GPS tracking integration
2. Payment processing
3. Customer notifications
4. Inventory management

## Best Practices

1. **Start Small**: Begin with manual tests before automation
2. **Monitor Everything**: Use WebSocket monitor during tests
3. **Check Logs**: Review application logs for errors
4. **Test Edge Cases**: Empty assets, invalid locations, etc.
5. **Performance Baseline**: Establish metrics for normal operation

Remember: The dummy location system simulates a real 18-hole golf course with realistic constraints and movement patterns!