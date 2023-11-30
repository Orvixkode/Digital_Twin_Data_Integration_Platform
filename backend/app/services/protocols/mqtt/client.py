import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
import aiomqtt
from app.core.config import settings
from app.database.connection import SessionLocal
from app.models import Equipment, SensorData, Sensor

logger = logging.getLogger("mqtt")

class MQTTService:
    """MQTT client for industrial equipment data collection"""
    
    def __init__(self):
        self.client: Optional[aiomqtt.Client] = None
        self.is_connected = False
        self.subscribed_topics: List[str] = []
        self.message_handlers: Dict[str, Callable] = {}
        
    async def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client = aiomqtt.Client(
                hostname=settings.MQTT_BROKER_HOST,
                port=settings.MQTT_BROKER_PORT,
                username=settings.MQTT_USERNAME or None,
                password=settings.MQTT_PASSWORD or None,
                keepalive=settings.MQTT_KEEPALIVE
            )
            
            await self.client.__aenter__()
            self.is_connected = True
            logger.info(f"Connected to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
            
            # Subscribe to configured topics
            await self._subscribe_to_topics()
            
            # Start message processing
            asyncio.create_task(self._process_messages())
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client and self.is_connected:
            try:
                await self.client.__aexit__(None, None, None)
                self.is_connected = False
                logger.info("Disconnected from MQTT broker")
            except Exception as e:
                logger.error(f"Error disconnecting from MQTT broker: {e}")
    
    async def _subscribe_to_topics(self):
        """Subscribe to configured MQTT topics"""
        for topic in settings.MQTT_TOPICS:
            try:
                await self.client.subscribe(topic, qos=settings.MQTT_QOS)
                self.subscribed_topics.append(topic)
                logger.info(f"Subscribed to MQTT topic: {topic}")
            except Exception as e:
                logger.error(f"Failed to subscribe to topic {topic}: {e}")
    
    async def _process_messages(self):
        """Process incoming MQTT messages"""
        try:
            async for message in self.client.messages:
                await self._handle_message(message)
        except Exception as e:
            logger.error(f"Error processing MQTT messages: {e}")
    
    async def _handle_message(self, message):
        """Handle individual MQTT message"""
        try:
            # Parse topic to extract equipment and sensor info
            topic_parts = message.topic.value.split('/')
            if len(topic_parts) >= 3:
                equipment_id = topic_parts[1]
                sensor_type = topic_parts[2]
                
                # Parse message payload
                payload = json.loads(message.payload.decode())
                
                # Extract sensor data
                value = payload.get('value')
                timestamp = payload.get('timestamp', datetime.utcnow().isoformat())
                quality = payload.get('quality', 'GOOD')
                
                if value is not None:
                    await self._store_sensor_data(
                        equipment_id=equipment_id,
                        sensor_type=sensor_type,
                        value=float(value),
                        timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
                        quality=quality,
                        source_protocol='MQTT'
                    )
                
        except Exception as e:
            logger.error(f"Error handling MQTT message from {message.topic}: {e}")
    
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
                
                logger.debug(f"Stored sensor data: {equipment_id}/{sensor_type} = {value}")
                
        except Exception as e:
            logger.error(f"Error storing sensor data: {e}")
    
    async def publish_command(self, equipment_id: str, command: str, payload: dict):
        """Publish command to equipment"""
        if not self.is_connected or not self.client:
            raise Exception("MQTT client not connected")
        
        topic = f"equipment/{equipment_id}/command/{command}"
        message = json.dumps(payload)
        
        try:
            await self.client.publish(topic, message, qos=settings.MQTT_QOS)
            logger.info(f"Published command to {topic}: {command}")
        except Exception as e:
            logger.error(f"Failed to publish command to {topic}: {e}")
            raise
    
    def add_message_handler(self, topic_pattern: str, handler: Callable):
        """Add custom message handler for specific topic pattern"""
        self.message_handlers[topic_pattern] = handler