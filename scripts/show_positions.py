#!/usr/bin/env python3
"""
Display current asset positions and status
Shows the randomized starting positions of all assets
"""
import requests
import json
from datetime import datetime
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000"

def get_asset_info():
    """Fetch and display current asset information"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/assets")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Unable to fetch assets (status code: {response.status_code})")
            return []
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return []

def display_course_map(assets):
    """Display a visual representation of the golf course with asset positions"""
    # Create a map of positions
    position_map = {}
    for asset in assets:
        location = str(asset['current_location'])
        if location not in position_map:
            position_map[location] = []
        position_map[location].append(asset)
    
    print("\n" + "="*70)
    print("GOLF COURSE MAP - Current Asset Positions")
    print("="*70)
    
    # Clubhouse
    print("\n🏢 CLUBHOUSE:")
    if "clubhouse" in position_map:
        for asset in position_map["clubhouse"]:
            print(f"   → {asset['name']} ({asset['asset_type']}) - {asset['status']}")
    else:
        print("   (empty)")
    
    # Front Nine
    print("\n⛳ FRONT NINE (Holes 1-9):")
    for hole in range(1, 10):
        hole_str = str(hole)
        if hole_str in position_map:
            print(f"   Hole {hole}:")
            for asset in position_map[hole_str]:
                status_icon = "🟢" if asset['status'] == 'available' else "🔴"
                print(f"      {status_icon} {asset['name']} ({asset['asset_type']})")
    
    # Back Nine
    print("\n⛳ BACK NINE (Holes 10-18):")
    for hole in range(10, 19):
        hole_str = str(hole)
        if hole_str in position_map:
            print(f"   Hole {hole}:")
            for asset in position_map[hole_str]:
                status_icon = "🟢" if asset['status'] == 'available' else "🔴"
                print(f"      {status_icon} {asset['name']} ({asset['asset_type']})")
    
    print("\n" + "="*70)

def display_asset_details(assets):
    """Display detailed information about each asset"""
    print("\nASSET DETAILS:")
    print("-"*70)
    print(f"{'Name':<15} {'Type':<15} {'Location':<10} {'Status':<12} {'Orders':<10}")
    print("-"*70)
    
    for asset in assets:
        name = asset['name']
        asset_type = asset['asset_type'].replace('_', ' ').title()
        location = str(asset['current_location'])
        status = asset['status']
        orders = len(asset.get('current_orders', []))
        
        # Add color coding for status
        if status == 'available':
            status_display = f"✅ {status}"
        elif status == 'on_delivery':
            status_display = f"🚗 {status}"
        else:
            status_display = f"❓ {status}"
        
        print(f"{name:<15} {asset_type:<15} {location:<10} {status_display:<20} {orders:<10}")
    
    print("-"*70)

def display_statistics(assets):
    """Display statistics about asset distribution"""
    total_assets = len(assets)
    available = sum(1 for a in assets if a['status'] == 'available')
    busy = sum(1 for a in assets if a['status'] == 'on_delivery')
    
    carts = [a for a in assets if a['asset_type'] == 'beverage_cart']
    staff = [a for a in assets if a['asset_type'] == 'delivery_staff']
    
    front_nine_assets = sum(1 for a in assets if str(a['current_location']).isdigit() and 1 <= int(a['current_location']) <= 9)
    back_nine_assets = sum(1 for a in assets if str(a['current_location']).isdigit() and 10 <= int(a['current_location']) <= 18)
    clubhouse_assets = sum(1 for a in assets if a['current_location'] == 'clubhouse')
    
    print("\nSTATISTICS:")
    print("-"*40)
    print(f"Total Assets: {total_assets}")
    print(f"  - Beverage Carts: {len(carts)}")
    print(f"  - Delivery Staff: {len(staff)}")
    print(f"\nAvailability:")
    print(f"  - Available: {available} ({available/total_assets*100:.1f}%)")
    print(f"  - Busy: {busy} ({busy/total_assets*100:.1f}%)")
    print(f"\nLocation Distribution:")
    print(f"  - Front Nine: {front_nine_assets}")
    print(f"  - Back Nine: {back_nine_assets}")
    print(f"  - Clubhouse: {clubhouse_assets}")
    print("-"*40)

def main():
    """Main function"""
    print(f"\n🏌️ Golf Course Delivery System - Asset Position Monitor")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get current asset information
    assets = get_asset_info()
    
    if not assets:
        print("\nNo assets found or unable to connect to API.")
        print("Make sure the system is running: make docker-up")
        return
    
    # Display the information
    display_course_map(assets)
    display_asset_details(assets)
    display_statistics(assets)
    
    print("\n💡 TIP: Assets start at randomized positions each time the system starts!")
    print("   Cart 1 (Reese): Random position on Front 9 (holes 1-9)")
    print("   Cart 2 (Bev-Cart 2): Random position on Back 9 (holes 10-18)")
    print("   Staff members: Random positions anywhere on the course")

if __name__ == "__main__":
    main()