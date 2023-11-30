import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from asyncua import Client, ua
from asyncua.common.subscription import SubHandler
from app.core.config import settings
from app.database.connection import SessionLocal
from app.models import Equipment, SensorData, Sensor

logger = logging.getLogger("opcua")

class OPCUASubscriptionHandler(SubHandler):
    """Handle OPC UA subscription events"""
    
    def __init__(self, opcua_service):
        self.opcua_service = opcua_service
    
    async def datachange_notification(self, node, val, data):
        """Handle data change notifications"""
        try:
            node_id = str(node)
            timestamp = datetime.utcnow()
            
            # Parse node ID to extract equipment and sensor info
            await self.opcua_service._process_node_data(node_id, val, timestamp)
            
        except Exception as e:
            logger.error(f"Error processing OPC UA data change: {e}")

class OPCUAService:
    """OPC UA client for industrial equipment data collection"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected = False
        self.subscription = None
        self.monitored_nodes: Dict[str, Any] = {}
        
    async def connect(self):
        """Connect to OPC UA server"""
        try:
            self.client = Client(url=settings.OPC_UA_ENDPOINT)
            
            # Set security policy if specified
            if settings.OPC_UA_SECURITY_POLICY != "None":
                await self.client.set_security_string(
                    f"Basic256Sha256,SignAndEncrypt,{settings.OPC_UA_SECURITY_POLICY}"
                )
            
            # Set authentication if provided
            if settings.OPC_UA_USERNAME:
                self.client.set_user(settings.OPC_UA_USERNAME)
                self.client.set_password(settings.OPC_UA_PASSWORD)
            
            # Connect to server
            await self.client.connect()
            self.is_connected = True
            logger.info(f"Connected to OPC UA server at {settings.OPC_UA_ENDPOINT}")
            
            # Setup subscriptions
            await self._setup_subscriptions()
            
        except Exception as e:
            logger.error(f"Failed to connect to OPC UA server: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from OPC UA server"""
        if self.client and self.is_connected:
            try:
                if self.subscription:
                    await self.subscription.delete()
                await self.client.disconnect()
                self.is_connected = False
                logger.info("Disconnected from OPC UA server")
            except Exception as e:
                logger.error(f"Error disconnecting from OPC UA server: {e}")
    
    async def _setup_subscriptions(self):
        """Setup OPC UA subscriptions for monitoring"""
        try:
            # Create subscription
            handler = OPCUASubscriptionHandler(self)
            self.subscription = await self.client.create_subscription(
                period=1000,  # 1 second
                handler=handler
            )
            
            # Get equipment from database and setup monitoring
            await self._setup_equipment_monitoring()
            
        except Exception as e:
            logger.error(f"Error setting up OPC UA subscriptions: {e}")
    
    async def _setup_equipment_monitoring(self):
        """Setup monitoring for OPC UA equipment"""
        try:
            with SessionLocal() as db:
                # Get all OPC UA equipment
                equipment_list = db.query(Equipment).filter(
                    Equipment.protocol == "OPC_UA",
                    Equipment.is_active == True
                ).all()
                
                for equipment in equipment_list:
                    await self._monitor_equipment(equipment)
                    
        except Exception as e:
            logger.error(f"Error setting up equipment monitoring: {e}")
    
    async def _monitor_equipment(self, equipment):
        """Monitor specific equipment nodes"""
        try:
            config = equipment.connection_config or {}
            node_ids = config.get('node_ids', [])
            
            for node_config in node_ids:
                node_id = node_config.get('node_id')
                sensor_type = node_config.get('sensor_type')
                
                if node_id:
                    # Get node object
                    node = self.client.get_node(node_id)
                    
                    # Create monitored item
                    handle = await self.subscription.subscribe_data_change(node)
                    
                    self.monitored_nodes[node_id] = {
                        'equipment_id': equipment.equipment_id,
                        'sensor_type': sensor_type,
                        'handle': handle,
                        'node': node
                    }
                    
                    logger.info(f"Monitoring OPC UA node: {node_id} for equipment {equipment.equipment_id}")
                    
        except Exception as e:
            logger.error(f"Error monitoring equipment {equipment.equipment_id}: {e}")
    
    async def _process_node_data(self, node_id: str, value: Any, timestamp: datetime):
        """Process data from monitored node"""
        try:
            node_info = self.monitored_nodes.get(node_id)
            if not node_info:
                return
            
            equipment_id = node_info['equipment_id']
            sensor_type = node_info['sensor_type']
            
            # Convert value to float if possible
            if isinstance(value, (int, float)):
                numeric_value = float(value)
            else:
                # Try to convert string to float
                try:
                    numeric_value = float(str(value))
                except ValueError:
                    logger.warning(f"Cannot convert OPC UA value to numeric: {value}")
                    return
            
            await self._store_sensor_data(
                equipment_id=equipment_id,
                sensor_type=sensor_type,
                value=numeric_value,
                timestamp=timestamp,
                quality='GOOD',
                source_protocol='OPC_UA'
            )
            
        except Exception as e:
            logger.error(f"Error processing OPC UA node data: {e}")
    
    async def _store_sensor_data(self, equipment_id: str, sensor_type: str, 
                               value: float, timestamp: datetime, quality: str, 
                               source_protocol: str):
        """Store sensor data in database"""
        try:
            with SessionLocal() as db:
                # Find equipment
                equipment = db.query(Equipment).filter(
                    Equipment.equipment_id == equipment_id
                ).first()
                
                if not equipment:
                    logger.warning(f"Equipment not found: {equipment_id}")
                    return
                
                # Find sensor
                sensor = db.query(Sensor).filter(
                    Sensor.equipment_id == equipment.id,
                    Sensor.type == sensor_type
                ).first()
                
                if not sensor:
                    logger.warning(f"Sensor not found: {equipment_id}/{sensor_type}")
                    return
                
                # Create sensor data record
                sensor_data = SensorData(
                    equipment_id=equipment.id,
                    sensor_id=sensor.id,
                    value=value,
                    quality=quality,
                    timestamp=timestamp,
                    source_protocol=source_protocol
                )
                
                db.add(sensor_data)
                db.commit()
                
                # Update equipment heartbeat
                equipment.last_heartbeat = datetime.utcnow()
                equipment.is_connected = True
                db.commit()
                
                logger.debug(f"Stored OPC UA data: {equipment_id}/{sensor_type} = {value}")
                
        except Exception as e:
            logger.error(f"Error storing OPC UA sensor data: {e}")
    
    async def read_node_value(self, node_id: str):
        """Read current value from OPC UA node"""
        if not self.is_connected or not self.client:
            raise Exception("OPC UA client not connected")
        
        try:
            node = self.client.get_node(node_id)
            value = await node.read_value()
            return value
        except Exception as e:
            logger.error(f"Error reading OPC UA node {node_id}: {e}")
            raise
    
    async def write_node_value(self, node_id: str, value: Any):
        """Write value to OPC UA node"""
        if not self.is_connected or not self.client:
            raise Exception("OPC UA client not connected")
        
        try:
            node = self.client.get_node(node_id)
            await node.write_value(value)
            logger.info(f"Written value to OPC UA node {node_id}: {value}")
        except Exception as e:
            logger.error(f"Error writing to OPC UA node {node_id}: {e}")
            raise
    
    async def browse_nodes(self, parent_node_id: str = "i=85"):
        """Browse OPC UA server nodes"""
        if not self.is_connected or not self.client:
            raise Exception("OPC UA client not connected")
        
        try:
            parent_node = self.client.get_node(parent_node_id)
            children = await parent_node.get_children()
            
            nodes = []
            for child in children:
                node_info = {
                    'node_id': str(child),
                    'display_name': await child.read_display_name(),
                    'node_class': await child.read_node_class(),
                    'data_type': None
                }
                
                # Get data type for variable nodes
                if node_info['node_class'] == ua.NodeClass.Variable:
                    try:
                        data_type = await child.read_data_type()
                        node_info['data_type'] = str(data_type)
                    except:
                        pass
                
                nodes.append(node_info)
            
            return nodes
            
        except Exception as e:
            logger.error(f"Error browsing OPC UA nodes: {e}")
            raise