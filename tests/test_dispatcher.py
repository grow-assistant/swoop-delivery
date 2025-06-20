"""
Tests for the dispatcher module
"""
import pytest
from unittest.mock import patch, MagicMock
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
        """Create dispatcher with sample assets and mocked prediction service"""
        dispatcher = Dispatcher(sample_assets)
        
        # Mock the prediction service to return consistent values
        mock_prediction_service = MagicMock()
        mock_prediction_service.predict_travel_time.return_value = 5.0  # 5 minutes travel time
        mock_prediction_service.predict_order_prep_time.return_value = 10.0  # 10 minutes prep time
        mock_prediction_service.predict_offer_acceptance_chance.return_value = 0.8  # 80% acceptance
        
        dispatcher.prediction_service = mock_prediction_service
        return dispatcher
    
    def test_calculate_eta_and_destination(self, dispatcher, sample_assets):
        """Test ETA calculation for an asset"""
        asset = sample_assets[0]  # Cart at hole 1
        order = Order(order_id="TEST_ETA", hole_number=4)
        eta, predicted_hole, prep_time = dispatcher.calculate_eta_and_destination(asset, order)
        
        # ETA should include prep time and travel time
        assert eta > 0  # Should have some ETA
        assert eta == 20.0  # 10 min prep + 5 min to clubhouse + 5 min to hole
        assert predicted_hole >= 4  # Player should have advanced based on ETA
        assert prep_time == 10.0  # Mocked prep time
    
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
    
    @patch('random.random', return_value=0.1)  # Mock to always accept (0.1 < any acceptance_chance > 0.5)
    def test_dispatch_order_success(self, mock_random, dispatcher):
        """Test successful order dispatch"""
        order = Order(order_id="TEST003", hole_number=3)
        assigned_asset = dispatcher.dispatch_order(order)
        
        assert assigned_asset is not None
        assert order.status == OrderStatus.ASSIGNED
        # With state-driven movement, assets not at clubhouse go to EN_ROUTE_TO_PICKUP first
        # Staff 1 is at clubhouse, so would go to WAITING_FOR_ORDER
        # Others would go to EN_ROUTE_TO_PICKUP
        assert assigned_asset.status in [AssetStatus.EN_ROUTE_TO_PICKUP, AssetStatus.WAITING_FOR_ORDER]
        assert order in assigned_asset.current_orders
    
    def test_dispatch_order_no_available_assets(self, dispatcher):
        """Test dispatch when no assets are available"""
        # Set all assets to busy
        for asset in dispatcher.assets:
            asset.status = AssetStatus.EN_ROUTE_TO_DROPOFF
        
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
    
    @patch('random.random', return_value=0.1)
    def test_state_transition_from_clubhouse(self, mock_random, dispatcher):
        """Test that assets at clubhouse transition to WAITING_FOR_ORDER"""
        # Staff 1 is at clubhouse
        staff1 = next(a for a in dispatcher.assets if a.asset_id == "staff1")
        order = Order(order_id="TEST006", hole_number=8)
        
        # Force selection of staff1 by making others unavailable
        for asset in dispatcher.assets:
            if asset != staff1:
                asset.status = AssetStatus.INACTIVE
        
        assigned_asset = dispatcher.dispatch_order(order)
        
        assert assigned_asset == staff1
        assert assigned_asset.status == AssetStatus.WAITING_FOR_ORDER
    
    @patch('random.random', return_value=0.1)
    def test_state_transition_not_at_clubhouse(self, mock_random, dispatcher):
        """Test that assets not at clubhouse transition to EN_ROUTE_TO_PICKUP"""
        # Cart 1 is at hole 1 (not clubhouse)
        cart1 = next(a for a in dispatcher.assets if a.asset_id == "cart1")
        order = Order(order_id="TEST007", hole_number=3)
        
        # Force selection of cart1 by making others unavailable
        for asset in dispatcher.assets:
            if asset != cart1:
                asset.status = AssetStatus.INACTIVE
        
        assigned_asset = dispatcher.dispatch_order(order)
        
        assert assigned_asset == cart1
        assert assigned_asset.status == AssetStatus.EN_ROUTE_TO_PICKUP