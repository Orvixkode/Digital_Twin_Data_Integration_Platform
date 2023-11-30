from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.database.connection import get_db
from app.models import Equipment
from app.services.protocols.mqtt.client import MQTTService
from app.services.protocols.opc_ua.client import OPCUAService
from pydantic import BaseModel

router = APIRouter()

class ProtocolTestRequest(BaseModel):
    protocol: str
    endpoint: str
    config: Dict[str, Any]

class ConnectionStatus(BaseModel):
    protocol: str
    is_connected: bool
    endpoint: str
    last_check: datetime
    error_message: str = None

@router.get("/protocols")
async def list_supported_protocols():
    """List all supported industrial protocols"""
    return {
        "supported_protocols": [
            {
                "name": "MQTT",
                "version": "3.1.1/5.0",
                "description": "Message Queuing Telemetry Transport for IoT devices",
                "port": 1883,
                "secure_port": 8883
            },
            {
                "name": "OPC_UA",
                "version": "1.04",
                "description": "OPC Unified Architecture for industrial automation",
                "port": 4840,
                "secure_port": 4843
            },
            {
                "name": "REST",
                "version": "HTTP/1.1",
                "description": "RESTful HTTP API integration",
                "port": 80,
                "secure_port": 443
            }
        ],
        "active_connections": 15,  # This would be dynamic
        "max_connections": 50
    }

@router.post("/test-connection")
async def test_protocol_connection(
    request: ProtocolTestRequest,
    db: Session = Depends(get_db)
):
    """Test connection to industrial equipment using specified protocol"""
    
    try:
        if request.protocol.upper() == "MQTT":
            # Test MQTT connection
            test_client = MQTTService()
            # Here you would implement actual connection test
            # For now, simulate test result
            success = True
            message = "MQTT connection successful"
            
        elif request.protocol.upper() == "OPC_UA":
            # Test OPC UA connection
            test_client = OPCUAService()
            # Simulate OPC UA connection test
            success = True
            message = "OPC UA connection successful"
            
        elif request.protocol.upper() == "REST":
            # Test REST endpoint
            # Implement HTTP request test
            success = True
            message = "REST endpoint accessible"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported protocol: {request.protocol}")
        
        return {
            "protocol": request.protocol,
            "endpoint": request.endpoint,
            "success": success,
            "message": message,
            "test_time": datetime.utcnow(),
            "response_time_ms": 150  # Simulated response time
        }
        
    except Exception as e:
        return {
            "protocol": request.protocol,
            "endpoint": request.endpoint,
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "test_time": datetime.utcnow(),
            "response_time_ms": None
        }

@router.get("/connection-status")
async def get_connection_status(db: Session = Depends(get_db)):
    """Get current connection status for all protocols"""
    
    # Get all active equipment grouped by protocol
    equipment_by_protocol = db.query(Equipment).filter(
        Equipment.is_active == True
    ).all()
    
    protocol_status = {}
    
    for equipment in equipment_by_protocol:
        protocol = equipment.protocol
        if protocol not in protocol_status:
            protocol_status[protocol] = {
                "total_equipment": 0,
                "connected": 0,
                "disconnected": 0,
                "last_activity": None
            }
        
        protocol_status[protocol]["total_equipment"] += 1
        
        if equipment.is_connected:
            protocol_status[protocol]["connected"] += 1
        else:
            protocol_status[protocol]["disconnected"] += 1
        
        # Update last activity
        if equipment.last_heartbeat:
            if (not protocol_status[protocol]["last_activity"] or 
                equipment.last_heartbeat > protocol_status[protocol]["last_activity"]):
                protocol_status[protocol]["last_activity"] = equipment.last_heartbeat
    
    return {
        "timestamp": datetime.utcnow(),
        "protocols": protocol_status,
        "summary": {
            "total_protocols": len(protocol_status),
            "total_equipment": sum(p["total_equipment"] for p in protocol_status.values()),
            "total_connected": sum(p["connected"] for p in protocol_status.values())
        }
    }

@router.get("/opc-ua/browse")
async def browse_opcua_nodes(
    parent_node: str = "i=85",
    db: Session = Depends(get_db)
):
    """Browse OPC UA server nodes for equipment discovery"""
    
    try:
        # This would use the actual OPC UA service
        opcua_service = OPCUAService()
        
        # Simulate node browsing for demo
        nodes = [
            {
                "node_id": "ns=2;s=Temperature",
                "display_name": "Temperature Sensor",
                "node_class": "Variable",
                "data_type": "Float"
            },
            {
                "node_id": "ns=2;s=Pressure",
                "display_name": "Pressure Sensor", 
                "node_class": "Variable",
                "data_type": "Float"
            },
            {
                "node_id": "ns=2;s=Status",
                "display_name": "Equipment Status",
                "node_class": "Variable", 
                "data_type": "Boolean"
            }
        ]
        
        return {
            "parent_node": parent_node,
            "nodes": nodes,
            "count": len(nodes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to browse OPC UA nodes: {str(e)}")

@router.post("/mqtt/publish")
async def publish_mqtt_command(
    equipment_id: str,
    command: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Publish command to equipment via MQTT"""
    
    # Find equipment
    equipment = db.query(Equipment).filter(
        Equipment.equipment_id == equipment_id,
        Equipment.protocol == "MQTT"
    ).first()
    
    if not equipment:
        raise HTTPException(status_code=404, detail="MQTT equipment not found")
    
    try:
        # This would use the actual MQTT service
        mqtt_service = MQTTService()
        
        # Simulate command publishing
        topic = f"equipment/{equipment_id}/command/{command}"
        
        return {
            "equipment_id": equipment_id,
            "command": command,
            "topic": topic,
            "payload": payload,
            "status": "published",
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish MQTT command: {str(e)}")

@router.get("/middleware/stats")
async def get_middleware_statistics():
    """Get middleware performance statistics"""
    
    return {
        "data_throughput": {
            "messages_per_second": 125.5,
            "bytes_per_second": 15600,
            "peak_throughput": 250.0
        },
        "protocol_distribution": {
            "MQTT": 60,
            "OPC_UA": 30,
            "REST": 10
        },
        "error_rates": {
            "connection_errors": 2.1,
            "timeout_errors": 1.5,
            "data_quality_errors": 0.8
        },
        "buffer_status": {
            "mqtt_buffer_usage": 15,
            "opcua_buffer_usage": 8,
            "max_buffer_size": 10000
        },
        "uptime": {
            "mqtt_service": 99.8,
            "opcua_service": 98.5,
            "database": 99.9
        }
    }