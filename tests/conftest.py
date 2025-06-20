"""
Pytest configuration for Golf Course Delivery System tests
"""
import sys
import os

# Add the parent directory to Python path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Disable import warnings for tests
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)