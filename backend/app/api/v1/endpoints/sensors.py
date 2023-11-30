from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database.connection import get_db
from app.models import Equipment, Sensor, SensorData
from pydantic import BaseModel

router = APIRouter()

class SensorCreate(BaseModel):
    sensor_id: str
    equipment_id: str
    name: str
    type: str
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    sampling_rate: Optional[int] = 1000

class SensorResponse(BaseModel):
    id: int
    sensor_id: str
    equipment_id: int
    name: str
    type: str
    unit: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    warning_threshold: Optional[float]
    critical_threshold: Optional[float]
    sampling_rate: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=SensorResponse)
async def create_sensor(
    sensor: SensorCreate,
    db: Session = Depends(get_db)
):
    """Create new sensor configuration"""
    # Find equipment
    equipment = db.query(Equipment).filter(
        Equipment.equipment_id == sensor.equipment_id
    ).first()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Check if sensor already exists
    existing = db.query(Sensor).filter(
        Sensor.sensor_id == sensor.sensor_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Sensor ID already exists")
    
    # Create sensor
    db_sensor = Sensor(
        sensor_id=sensor.sensor_id,
        equipment_id=equipment.id,
        name=sensor.name,
        type=sensor.type,
        unit=sensor.unit,
        min_value=sensor.min_value,
        max_value=sensor.max_value,
        warning_threshold=sensor.warning_threshold,
        critical_threshold=sensor.critical_threshold,
        sampling_rate=sensor.sampling_rate
    )
    
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    
    return db_sensor

@router.get("/", response_model=List[SensorResponse])
async def list_sensors(
    equipment_id: Optional[str] = Query(None),
    sensor_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """List sensors with filtering"""
    query = db.query(Sensor).join(Equipment)
    
    if equipment_id:
        query = query.filter(Equipment.equipment_id == equipment_id)
    
    if sensor_type:
        query = query.filter(Sensor.type == sensor_type)
    
    sensors = query.offset(skip).limit(limit).all()
    return sensors

@router.get("/{sensor_id}", response_model=SensorResponse)
async def get_sensor(
    sensor_id: str,
    db: Session = Depends(get_db)
):
    """Get specific sensor details"""
    sensor = db.query(Sensor).filter(Sensor.sensor_id == sensor_id).first()
    
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    return sensor