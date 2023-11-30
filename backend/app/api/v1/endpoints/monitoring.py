from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.models import Equipment, Sensor, SensorData, Alert
from pydantic import BaseModel

router = APIRouter()

class DashboardOverview(BaseModel):
    total_equipment: int
    active_equipment: int
    connected_equipment: int
    total_alerts: int
    critical_alerts: int
    data_points_today: int
    protocols_summary: Dict[str, int]

@router.get("/dashboard", response_model=DashboardOverview)
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """Get comprehensive dashboard overview for monitoring interface"""
    
    # Equipment statistics
    total_equipment = db.query(func.count(Equipment.id)).scalar()
    active_equipment = db.query(func.count(Equipment.id)).filter(Equipment.is_active == True).scalar()
    connected_equipment = db.query(func.count(Equipment.id)).filter(Equipment.is_connected == True).scalar()
    
    # Alert statistics
    total_alerts = db.query(func.count(Alert.id)).filter(Alert.is_acknowledged == False).scalar()
    critical_alerts = db.query(func.count(Alert.id)).filter(
        Alert.severity == "CRITICAL",
        Alert.is_acknowledged == False
    ).scalar()
    
    # Data points today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    data_points_today = db.query(func.count(SensorData.id)).filter(
        SensorData.timestamp >= today
    ).scalar()
    
    # Protocol distribution
    protocol_stats = db.query(
        Equipment.protocol,
        func.count(Equipment.id)
    ).filter(Equipment.is_active == True).group_by(Equipment.protocol).all()
    
    protocols_summary = {stat[0]: stat[1] for stat in protocol_stats}
    
    return DashboardOverview(
        total_equipment=total_equipment or 0,
        active_equipment=active_equipment or 0,
        connected_equipment=connected_equipment or 0,
        total_alerts=total_alerts or 0,
        critical_alerts=critical_alerts or 0,
        data_points_today=data_points_today or 0,
        protocols_summary=protocols_summary
    )

@router.get("/realtime-data")
async def get_realtime_data(
    equipment_ids: Optional[List[str]] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """Get latest sensor readings for real-time monitoring"""
    
    # Get latest data points for each sensor
    subquery = db.query(
        SensorData.sensor_id,
        func.max(SensorData.timestamp).label('max_timestamp')
    ).group_by(SensorData.sensor_id).subquery()
    
    query = db.query(SensorData).join(Equipment).join(Sensor).join(
        subquery,
        (SensorData.sensor_id == subquery.c.sensor_id) & 
        (SensorData.timestamp == subquery.c.max_timestamp)
    )
    
    if equipment_ids:
        query = query.filter(Equipment.equipment_id.in_(equipment_ids))
    
    latest_readings = query.limit(limit).all()
    
    realtime_data = []
    for reading in latest_readings:
        # Determine status based on thresholds
        sensor = reading.sensor
        status = "NORMAL"
        
        if sensor.critical_threshold and reading.value > sensor.critical_threshold:
            status = "CRITICAL"
        elif sensor.warning_threshold and reading.value > sensor.warning_threshold:
            status = "WARNING"
        
        realtime_data.append({
            "equipment_id": reading.equipment.equipment_id,
            "equipment_name": reading.equipment.name,
            "sensor_id": reading.sensor.sensor_id,
            "sensor_type": sensor.type,
            "value": reading.value,
            "unit": sensor.unit,
            "timestamp": reading.timestamp,
            "quality": reading.quality,
            "status": status,
            "thresholds": {
                "warning": sensor.warning_threshold,
                "critical": sensor.critical_threshold
            }
        })
    
    return {
        "timestamp": datetime.utcnow(),
        "count": len(realtime_data),
        "data": realtime_data
    }

@router.get("/alerts")
async def get_active_alerts(
    severity: Optional[str] = Query(None),
    equipment_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """Get active alerts for monitoring"""
    
    query = db.query(Alert).filter(Alert.is_acknowledged == False)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    if equipment_id:
        query = query.join(Equipment).filter(Equipment.equipment_id == equipment_id)
    
    alerts = query.order_by(desc(Alert.triggered_at)).offset(skip).limit(limit).all()
    
    return {
        "alerts": [
            {
                "alert_id": alert.alert_id,
                "equipment_id": alert.equipment_id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "triggered_at": alert.triggered_at,
                "age_minutes": int((datetime.utcnow() - alert.triggered_at).total_seconds() / 60)
            }
            for alert in alerts
        ],
        "total_count": len(alerts)
    }

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str,
    db: Session = Depends(get_db)
):
    """Acknowledge an alert"""
    
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_acknowledged = True
    alert.acknowledged_by = acknowledged_by
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Alert {alert_id} acknowledged by {acknowledged_by}"}

@router.get("/equipment-health")
async def get_equipment_health(
    db: Session = Depends(get_db)
):
    """Get health status of all equipment"""
    
    equipment_list = db.query(Equipment).filter(Equipment.is_active == True).all()
    
    health_data = []
    for equipment in equipment_list:
        # Get latest heartbeat
        time_since_heartbeat = None
        if equipment.last_heartbeat:
            time_since_heartbeat = (datetime.utcnow() - equipment.last_heartbeat).total_seconds()
        
        # Determine health status
        health_status = "UNKNOWN"
        if equipment.is_connected:
            if time_since_heartbeat and time_since_heartbeat < 300:  # 5 minutes
                health_status = "HEALTHY"
            else:
                health_status = "DEGRADED"
        else:
            health_status = "OFFLINE"
        
        # Get recent data quality
        recent_data = db.query(SensorData).filter(
            SensorData.equipment_id == equipment.id,
            SensorData.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).all()
        
        data_quality = "UNKNOWN"
        if recent_data:
            good_quality = sum(1 for d in recent_data if d.quality == "GOOD")
            quality_ratio = good_quality / len(recent_data)
            
            if quality_ratio >= 0.9:
                data_quality = "EXCELLENT"
            elif quality_ratio >= 0.7:
                data_quality = "GOOD"
            else:
                data_quality = "POOR"
        
        health_data.append({
            "equipment_id": equipment.equipment_id,
            "name": equipment.name,
            "type": equipment.type,
            "protocol": equipment.protocol,
            "health_status": health_status,
            "is_connected": equipment.is_connected,
            "last_heartbeat": equipment.last_heartbeat,
            "data_quality": data_quality,
            "recent_data_points": len(recent_data)
        })
    
    return {
        "timestamp": datetime.utcnow(),
        "equipment": health_data,
        "summary": {
            "total": len(health_data),
            "healthy": len([e for e in health_data if e["health_status"] == "HEALTHY"]),
            "degraded": len([e for e in health_data if e["health_status"] == "DEGRADED"]),
            "offline": len([e for e in health_data if e["health_status"] == "OFFLINE"])
        }
    }

@router.get("/performance-metrics")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get system performance metrics"""
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Data ingestion rate
    data_points = db.query(func.count(SensorData.id)).filter(
        SensorData.timestamp >= start_time
    ).scalar()
    
    ingestion_rate = (data_points or 0) / hours  # points per hour
    
    # Protocol distribution of recent data
    protocol_data = db.query(
        SensorData.source_protocol,
        func.count(SensorData.id)
    ).filter(
        SensorData.timestamp >= start_time
    ).group_by(SensorData.source_protocol).all()
    
    protocol_breakdown = {proto[0]: proto[1] for proto in protocol_data}
    
    # Quality metrics
    quality_data = db.query(
        SensorData.quality,
        func.count(SensorData.id)
    ).filter(
        SensorData.timestamp >= start_time
    ).group_by(SensorData.quality).all()
    
    quality_breakdown = {qual[0]: qual[1] for qual in quality_data}
    
    # Connection stability
    connection_events = db.query(Equipment).filter(
        Equipment.last_heartbeat >= start_time
    ).count()
    
    return {
        "time_period": {
            "start": start_time,
            "end": end_time,
            "hours": hours
        },
        "data_ingestion": {
            "total_points": data_points or 0,
            "points_per_hour": round(ingestion_rate, 2),
            "points_per_minute": round(ingestion_rate / 60, 2)
        },
        "protocol_breakdown": protocol_breakdown,
        "quality_metrics": quality_breakdown,
        "connection_stability": {
            "active_connections": connection_events,
            "connection_rate": round(connection_events / hours, 2)
        }
    }