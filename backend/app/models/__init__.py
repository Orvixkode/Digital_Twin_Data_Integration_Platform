from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class Equipment(Base):
    """Industrial equipment model"""
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(100), nullable=False)  # e.g., "pump", "motor", "sensor"
    manufacturer = Column(String(100))
    model = Column(String(100))
    location = Column(String(200))
    description = Column(Text)
    
    # Connection details
    protocol = Column(String(20), nullable=False)  # "OPC_UA", "MQTT", "REST"
    endpoint = Column(String(500))
    connection_config = Column(JSON)  # Protocol-specific configuration
    
    # Status
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_heartbeat = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sensors = relationship("Sensor", back_populates="equipment")
    data_points = relationship("SensorData", back_populates="equipment")

class Sensor(Base):
    """Sensor configuration model"""
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), unique=True, index=True, nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # "temperature", "pressure", "vibration"
    unit = Column(String(20))  # "°C", "bar", "Hz"
    
    # Thresholds and limits
    min_value = Column(Float)
    max_value = Column(Float)
    warning_threshold = Column(Float)
    critical_threshold = Column(Float)
    
    # Configuration
    sampling_rate = Column(Integer, default=1000)  # milliseconds
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    equipment = relationship("Equipment", back_populates="sensors")
    data_points = relationship("SensorData", back_populates="sensor")

class SensorData(Base):
    """Real-time sensor data model"""
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    
    # Data
    value = Column(Float, nullable=False)
    quality = Column(String(20), default="GOOD")  # "GOOD", "BAD", "UNCERTAIN"
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Processing flags
    is_processed = Column(Boolean, default=False)
    is_anomaly = Column(Boolean, default=False)
    
    # Metadata
    source_protocol = Column(String(20))
    batch_id = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    equipment = relationship("Equipment", back_populates="data_points")
    sensor = relationship("Sensor", back_populates="data_points")

class Alert(Base):
    """Alert and notification model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), unique=True, default=lambda: str(uuid.uuid4()))
    
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    sensor_id = Column(Integer, ForeignKey("sensors.id"))
    
    # Alert details
    severity = Column(String(20), nullable=False)  # "INFO", "WARNING", "CRITICAL"
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Timestamps
    triggered_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DataProcessingJob(Base):
    """Data processing job tracking"""
    __tablename__ = "data_processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, default=lambda: str(uuid.uuid4()))
    
    # Job details
    job_type = Column(String(50), nullable=False)  # "aggregation", "anomaly_detection", "export"
    status = Column(String(20), default="PENDING")  # "PENDING", "RUNNING", "COMPLETED", "FAILED"
    
    # Configuration
    config = Column(JSON)
    equipment_filter = Column(JSON)  # Equipment IDs to process
    time_range_start = Column(DateTime(timezone=True))
    time_range_end = Column(DateTime(timezone=True))
    
    # Results
    records_processed = Column(Integer, default=0)
    error_message = Column(Text)
    result_file_path = Column(String(500))
    
    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())