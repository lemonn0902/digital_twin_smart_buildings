from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Building(Base):
    __tablename__ = "buildings"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String)
    total_area_m2 = Column(Float)
    num_floors = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Relationships
    zones = relationship("Zone", back_populates="building", cascade="all, delete-orphan")
    simulations = relationship("Simulation", back_populates="building")


class Zone(Base):
    __tablename__ = "zones"
    
    id = Column(String, primary_key=True)
    building_id = Column(String, ForeignKey("buildings.id"), nullable=False)
    name = Column(String, nullable=False)
    floor = Column(Integer, nullable=False)
    area_m2 = Column(Float, nullable=False)
    zone_type = Column(String)  # e.g., "office", "meeting_room", "corridor"
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, default={})
    
    # Relationships
    building = relationship("Building", back_populates="zones")
    neighbors = relationship(
        "ZoneConnection",
        foreign_keys="ZoneConnection.zone_a_id",
        back_populates="zone_a"
    )


class ZoneConnection(Base):
    __tablename__ = "zone_connections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_a_id = Column(String, ForeignKey("zones.id"), nullable=False)
    zone_b_id = Column(String, ForeignKey("zones.id"), nullable=False)
    connection_type = Column(String)  # e.g., "door", "wall", "adjacent"
    
    zone_a = relationship("Zone", foreign_keys=[zone_a_id])


class Simulation(Base):
    __tablename__ = "simulations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String, ForeignKey("buildings.id"), nullable=False)
    scenario = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    resolution_minutes = Column(Integer, nullable=False)
    status = Column(String, default="completed")  # "running", "completed", "failed"
    created_at = Column(DateTime, default=datetime.utcnow)
    results_metadata = Column(JSON, default={})
    
    # Relationships
    building = relationship("Building", back_populates="simulations")


class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String, nullable=False)
    zone_id = Column(String)
    metric = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    value = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Suggestion(Base):
    __tablename__ = "suggestions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String, nullable=False)
    suggestion_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    estimated_savings_kwh = Column(Float)
    comfort_risk = Column(String)  # "low", "medium", "high"
    status = Column(String, default="pending")  # "pending", "accepted", "rejected", "applied"
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_at = Column(DateTime)
    metadata = Column(JSON, default={})


