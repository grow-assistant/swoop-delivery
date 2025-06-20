"""
Database configuration and models for persistent storage
"""
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Enum, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool
import os
from datetime import datetime
from decouple import config

# Database configuration
DATABASE_URL = config("DATABASE_URL", default="sqlite:///./golf_delivery.db")

# Create engine lazily to avoid connection during imports
engine = None

def get_engine():
    """Get or create the database engine"""
    global engine
    if engine is None:
        if DATABASE_URL.startswith("sqlite"):
            engine = create_engine(
                DATABASE_URL,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            engine = create_engine(DATABASE_URL)
    return engine

# Create session factory (will bind to engine when needed)
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

# Create base
Base = declarative_base()

# Database Models
class DBAsset(Base):
    __tablename__ = "assets"
    
    asset_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # "beverage_cart" or "delivery_staff"
    status = Column(String, default="available")
    current_location = Column(String, default="clubhouse")
    loop = Column(String, nullable=True)  # Only for beverage carts
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = relationship("DBOrder", back_populates="assigned_asset")

class DBOrder(Base):
    __tablename__ = "orders"
    
    order_id = Column(String, primary_key=True)
    hole_number = Column(Integer, nullable=False)
    status = Column(String, default="pending")
    items = Column(JSON, default=[])
    special_instructions = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    dispatched_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Foreign keys
    assigned_to_id = Column(String, ForeignKey("assets.asset_id"), nullable=True)
    
    # Relationships
    assigned_asset = relationship("DBAsset", back_populates="orders")

class DBDeliveryMetric(Base):
    __tablename__ = "delivery_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.order_id"))
    asset_id = Column(String, ForeignKey("assets.asset_id"))
    prep_time = Column(Float)
    travel_time = Column(Float)
    total_time = Column(Float)
    predicted_eta = Column(Float)
    actual_delivery_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database initialization
async def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=get_engine())

# Dependency
def get_db():
    """Get database session"""
    # Bind the session to engine only when needed
    SessionLocal.configure(bind=get_engine())
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()