"""
Pytest configuration for Golf Course Delivery System tests
"""
import sys
import os

# Add the parent directory to Python path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set test environment variables before any imports
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'  # Use in-memory SQLite for tests
os.environ['TESTING'] = 'true'

# Disable import warnings for tests
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)