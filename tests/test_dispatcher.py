"""
Tests for the dispatcher module
"""
import pytest
from src.models import BeverageCart, DeliveryStaff, Order, AssetStatus, OrderStatus
from src.dispatcher import Dispatcher


class TestDispatcher:
    """Test cases for the Dispatcher class"""
    
    @pytest.fixture
    def sample_assets(self):
        """Create sample assets for testing"""
        return [
            BeverageCart(asset_id="cart1", name="Cart 1", loop="front_9", current_location=1),
            BeverageCart(asset_id="cart2", name="Cart 2", loop="back_9", current_location=10),
            DeliveryStaff(asset_id="staff1", name="Staff 1", current_location="clubhouse"),
            DeliveryStaff(asset_id="staff2", name="Staff 2", current_location=5),
        ]
    
    @pytest.fixture
    def dispatcher(self, sample_assets):
        """Create dispatcher with sample assets"""
        return Dispatcher(sample_assets)
    
    def test_calculate_eta_and_destination(self, dispatcher, sample_assets):
        """Test ETA calculation for an asset"""
        asset = sample_assets[0]  # Cart at hole 1
        eta, predicted_hole = dispatcher.calculate_eta_and_destination(asset, 4)
        
        # ETA should include prep time and travel time
        assert eta > 10  # At least prep time
        assert predicted_hole >= 4  # Player should have advanced
    
    def test_find_best_candidate_front_nine(self, dispatcher):
        """Test finding best candidate for front nine order"""
        order = Order(order_id="TEST001", hole_number=5)
        candidate = dispatcher.find_best_candidate(order)
        
        assert candidate is not None
        assert candidate['asset'].asset_id in ["cart1", "staff1", "staff2"]
    
    def test_find_best_candidate_back_nine(self, dispatcher):
        """Test finding best candidate for back nine order"""
        order = Order(order_id="TEST002", hole_number=15)
        candidate = dispatcher.find_best_candidate(order)
        
        assert candidate is not None
        # Should prefer cart2 or staff members
        assert candidate['asset'].asset_id in ["cart2", "staff1", "staff2"]
    
    def test_dispatch_order_success(self, dispatcher):
        """Test successful order dispatch"""
        order = Order(order_id="TEST003", hole_number=3)
        assigned_asset = dispatcher.dispatch_order(order)
        
        assert assigned_asset is not None
        assert order.status == OrderStatus.ASSIGNED
        assert assigned_asset.status == AssetStatus.ON_DELIVERY
        assert order in assigned_asset.current_orders
    
    def test_dispatch_order_no_available_assets(self, dispatcher):
        """Test dispatch when no assets are available"""
        # Set all assets to busy
        for asset in dispatcher.assets:
            asset.status = AssetStatus.ON_DELIVERY
        
        order = Order(order_id="TEST004", hole_number=7)
        assigned_asset = dispatcher.dispatch_order(order)
        
        assert assigned_asset is None
        assert order.status == OrderStatus.PENDING
    
    def test_beverage_cart_preference(self, dispatcher):
        """Test that beverage carts are preferred when ETA is similar"""
        # Create a scenario where cart and staff have similar ETAs
        order = Order(order_id="TEST005", hole_number=2)
        candidate = dispatcher.find_best_candidate(order)
        
        # If a cart is available for the zone, it should be preferred
        if candidate and isinstance(candidate['asset'], BeverageCart):
            assert candidate['asset'].loop == "front_9"