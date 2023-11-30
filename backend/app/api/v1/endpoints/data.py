from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from app.database.connection import get_db
from app.models import Equipment, Sensor, SensorData, DataProcessingJob
from pydantic import BaseModel

router = APIRouter()

class DataQuery(BaseModel):
    equipment_ids: Optional[List[str]] = None
    sensor_types: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    aggregation: Optional[str] = "raw"  # raw, avg, min, max, count
    interval: Optional[str] = "1h"  # 1m, 5m, 15m, 1h, 1d

class DataExportRequest(BaseModel):
    equipment_ids: Optional[List[str]] = None
    sensor_types: Optional[List[str]] = None
    start_time: datetime
    end_time: datetime
    format: str = "csv"  # csv, json, parquet
    include_metadata: bool = True

class AnomalyDetectionRequest(BaseModel):
    equipment_ids: Optional[List[str]] = None
    sensor_types: Optional[List[str]] = None
    lookback_hours: int = 24
    threshold_multiplier: float = 2.0

@router.post("/query")
async def query_sensor_data(
    query: DataQuery,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, le=10000),
    db: Session = Depends(get_db)
):
    """Query and explore sensor data with filtering and aggregation"""
    
    # Build base query
    base_query = db.query(SensorData).join(Equipment).join(Sensor)
    
    # Apply filters
    if query.equipment_ids:
        base_query = base_query.filter(Equipment.equipment_id.in_(query.equipment_ids))
    
    if query.sensor_types:
        base_query = base_query.filter(Sensor.type.in_(query.sensor_types))
    
    if query.start_time:
        base_query = base_query.filter(SensorData.timestamp >= query.start_time)
    
    if query.end_time:
        base_query = base_query.filter(SensorData.timestamp <= query.end_time)
    
    # Apply aggregation
    if query.aggregation == "raw":
        results = base_query.order_by(SensorData.timestamp.desc()).offset(skip).limit(limit).all()
        
        return {
            "data": [
                {
                    "equipment_id": data.equipment.equipment_id,
                    "sensor_type": data.sensor.type,
                    "value": data.value,
                    "timestamp": data.timestamp,
                    "quality": data.quality
                }
                for data in results
            ],
            "aggregation": "raw",
            "count": len(results)
        }
    
    else:
        # Perform aggregation
        agg_func = {
            "avg": func.avg(SensorData.value),
            "min": func.min(SensorData.value),
            "max": func.max(SensorData.value),
            "count": func.count(SensorData.value)
        }.get(query.aggregation, func.avg(SensorData.value))
        
        # Time-based grouping
        time_group = func.date_trunc(query.interval.replace('h', ' hour').replace('m', ' minute').replace('d', ' day'), SensorData.timestamp)
        
        results = base_query.with_entities(
            Equipment.equipment_id,
            Sensor.type,
            time_group.label('time_bucket'),
            agg_func.label('aggregated_value')
        ).group_by(
            Equipment.equipment_id,
            Sensor.type,
            time_group
        ).order_by(time_group.desc()).offset(skip).limit(limit).all()
        
        return {
            "data": [
                {
                    "equipment_id": result.equipment_id,
                    "sensor_type": result.type,
                    "time_bucket": result.time_bucket,
                    "value": float(result.aggregated_value),
                }
                for result in results
            ],
            "aggregation": query.aggregation,
            "interval": query.interval,
            "count": len(results)
        }

@router.post("/export")
async def export_data(
    export_request: DataExportRequest,
    db: Session = Depends(get_db)
):
    """Export sensor data for analysis"""
    
    # Create processing job
    job = DataProcessingJob(
        job_type="export",
        config={
            "format": export_request.format,
            "include_metadata": export_request.include_metadata
        },
        equipment_filter=export_request.equipment_ids,
        time_range_start=export_request.start_time,
        time_range_end=export_request.end_time,
        status="PENDING"
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Here you would typically queue the job for background processing
    # For now, return job info
    
    return {
        "job_id": job.job_id,
        "status": "QUEUED",
        "message": "Export job created and queued for processing",
        "estimated_completion": datetime.utcnow() + timedelta(minutes=5)
    }

@router.get("/statistics")
async def get_data_statistics(
    equipment_id: Optional[str] = Query(None),
    sensor_type: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    db: Session = Depends(get_db)
):
    """Get statistical summary of sensor data"""
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Build query
    query = db.query(SensorData).join(Equipment).join(Sensor)
    query = query.filter(SensorData.timestamp >= start_time)
    
    if equipment_id:
        query = query.filter(Equipment.equipment_id == equipment_id)
    
    if sensor_type:
        query = query.filter(Sensor.type == sensor_type)
    
    # Get aggregated statistics
    stats = query.with_entities(
        func.count(SensorData.value).label('count'),
        func.avg(SensorData.value).label('average'),
        func.min(SensorData.value).label('minimum'),
        func.max(SensorData.value).label('maximum'),
        func.stddev(SensorData.value).label('std_dev')
    ).first()
    
    # Get data quality metrics
    quality_stats = query.with_entities(
        SensorData.quality,
        func.count(SensorData.quality).label('count')
    ).group_by(SensorData.quality).all()
    
    return {
        "time_range": {
            "start": start_time,
            "end": end_time,
            "hours": hours
        },
        "filters": {
            "equipment_id": equipment_id,
            "sensor_type": sensor_type
        },
        "statistics": {
            "count": stats.count or 0,
            "average": float(stats.average) if stats.average else 0,
            "minimum": float(stats.minimum) if stats.minimum else 0,
            "maximum": float(stats.maximum) if stats.maximum else 0,
            "std_deviation": float(stats.std_dev) if stats.std_dev else 0
        },
        "quality_distribution": {
            quality.quality: quality.count for quality in quality_stats
        }
    }

@router.post("/anomaly-detection")
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_db)
):
    """Detect anomalies in sensor data using statistical methods"""
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=request.lookback_hours)
    
    # Build query
    query = db.query(SensorData).join(Equipment).join(Sensor)
    query = query.filter(SensorData.timestamp >= start_time)
    
    if request.equipment_ids:
        query = query.filter(Equipment.equipment_id.in_(request.equipment_ids))
    
    if request.sensor_types:
        query = query.filter(Sensor.type.in_(request.sensor_types))
    
    # Get data for analysis
    data_points = query.all()
    
    if len(data_points) < 10:
        return {
            "message": "Insufficient data for anomaly detection",
            "anomalies": []
        }
    
    # Group by equipment and sensor for individual analysis
    grouped_data = {}
    for point in data_points:
        key = f"{point.equipment.equipment_id}_{point.sensor.type}"
        if key not in grouped_data:
            grouped_data[key] = []
        grouped_data[key].append(point)
    
    anomalies = []
    
    for key, points in grouped_data.items():
        if len(points) < 5:
            continue
            
        values = [p.value for p in points]
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        threshold = request.threshold_multiplier * std_val
        
        for point in points:
            if abs(point.value - mean_val) > threshold:
                anomalies.append({
                    "equipment_id": point.equipment.equipment_id,
                    "sensor_type": point.sensor.type,
                    "value": point.value,
                    "expected_range": [mean_val - threshold, mean_val + threshold],
                    "deviation": abs(point.value - mean_val) / std_val,
                    "timestamp": point.timestamp,
                    "severity": "HIGH" if abs(point.value - mean_val) > 3 * std_val else "MEDIUM"
                })
    
    # Sort by deviation (most anomalous first)
    anomalies.sort(key=lambda x: x["deviation"], reverse=True)
    
    return {
        "analysis_period": {
            "start": start_time,
            "end": end_time,
            "hours": request.lookback_hours
        },
        "threshold_multiplier": request.threshold_multiplier,
        "total_points_analyzed": len(data_points),
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies[:50]  # Return top 50 anomalies
    }

@router.get("/jobs/{job_id}")
async def get_processing_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """Get status of a data processing job"""
    
    job = db.query(DataProcessingJob).filter(
        DataProcessingJob.job_id == job_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "job_type": job.job_type,
        "status": job.status,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "records_processed": job.records_processed,
        "result_file_path": job.result_file_path,
        "error_message": job.error_message
    }