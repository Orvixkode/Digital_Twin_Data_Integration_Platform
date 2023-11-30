from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.models import Equipment, Sensor, SensorData
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for API
class EquipmentCreate(BaseModel):
    equipment_id: str
    name: str
    type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    protocol: str
    endpoint: Optional[str] = None
    connection_config: Optional[dict] = None

class EquipmentResponse(BaseModel):
    id: int
    equipment_id: str
    name: str
    type: str
    manufacturer: Optional[str]
    model: Optional[str]
    location: Optional[str]
    description: Optional[str]
    protocol: str
    endpoint: Optional[str]
    is_active: bool
    is_connected: bool
    last_heartbeat: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    endpoint: Optional[str] = None
    connection_config: Optional[dict] = None
    is_active: Optional[bool] = None

@router.get("/", response_model=List[EquipmentResponse])
async def list_equipment(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    protocol: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_connected: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List all industrial equipment with filtering options"""
    query = db.query(Equipment)
    
    if protocol:
        query = query.filter(Equipment.protocol == protocol)
    if is_active is not None:
        query = query.filter(Equipment.is_active == is_active)
    if is_connected is not None:
        query = query.filter(Equipment.is_connected == is_connected)
    
    equipment_list = query.offset(skip).limit(limit).all()
    return equipment_list

@router.post("/", response_model=EquipmentResponse)
async def create_equipment(
    equipment: EquipmentCreate,
    db: Session = Depends(get_db)
):
    """Register new industrial equipment"""
    # Check if equipment ID already exists
    existing = db.query(Equipment).filter(
        Equipment.equipment_id == equipment.equipment_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Equipment with ID {equipment.equipment_id} already exists"
        )
    
    # Create new equipment
    db_equipment = Equipment(**equipment.dict())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    
    return db_equipment

@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """Get specific equipment details"""
    equipment = db.query(Equipment).filter(
        Equipment.equipment_id == equipment_id
    ).first()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    return equipment

@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: str,
    equipment_update: EquipmentUpdate,
    db: Session = Depends(get_db)
):
    """Update equipment configuration"""
    equipment = db.query(Equipment).filter(
        Equipment.equipment_id == equipment_id
    ).first()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Update fields
    update_data = equipment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(equipment, field, value)
    
    db.commit()
    db.refresh(equipment)
    
    return equipment

@router.delete("/{equipment_id}")
async def delete_equipment(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """Delete equipment (soft delete by setting inactive)"""
    equipment = db.query(Equipment).filter(
        Equipment.equipment_id == equipment_id
    ).first()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    equipment.is_active = False
    db.commit()
    
    return {"message": f"Equipment {equipment_id} deactivated"}

@router.get("/{equipment_id}/status")
async def get_equipment_status(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """Get real-time equipment status"""
    equipment = db.query(Equipment).filter(
        Equipment.equipment_id == equipment_id
    ).first()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Get latest sensor readings
    latest_data = db.query(SensorData).filter(
        SensorData.equipment_id == equipment.id
    ).order_by(SensorData.timestamp.desc()).limit(10).all()
    
    # Calculate uptime
    uptime_hours = 0
    if equipment.last_heartbeat:
        uptime_hours = (datetime.utcnow() - equipment.last_heartbeat).total_seconds() / 3600
    
    return {
        "equipment_id": equipment_id,
        "is_connected": equipment.is_connected,
        "last_heartbeat": equipment.last_heartbeat,
        "uptime_hours": uptime_hours,
        "protocol": equipment.protocol,
        "latest_readings": [
            {
                "sensor_id": data.sensor_id,
                "value": data.value,
                "timestamp": data.timestamp,
                "quality": data.quality
            }
            for data in latest_data
        ]
    }

@router.post("/{equipment_id}/connect")
async def connect_equipment(
    equipment_id: str,
    db: Session = Depends(get_db)
):
    """Manually trigger equipment connection"""
    equipment = db.query(Equipment).filter(
        Equipment.equipment_id == equipment_id
    ).first()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Here you would trigger the actual connection logic
    # For now, just update the status
    equipment.is_connected = True
    equipment.last_heartbeat = datetime.utcnow()
    db.commit()
    
    return {"message": f"Connection initiated for equipment {equipment_id}"}