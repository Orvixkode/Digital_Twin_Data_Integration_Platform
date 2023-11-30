from pydantic import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Application settings
    APP_NAME: str = "Digital Twin Data Integration Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/digitwin_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis for caching and session management
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OPC UA Configuration
    OPC_UA_ENDPOINT: str = "opc.tcp://localhost:4840/freeopcua/server/"
    OPC_UA_USERNAME: str = ""
    OPC_UA_PASSWORD: str = ""
    OPC_UA_SECURITY_POLICY: str = "None"
    
    # MQTT Configuration
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_QOS: int = 1
    MQTT_KEEPALIVE: int = 60
    MQTT_TOPICS: List[str] = [
        "equipment/+/temperature",
        "equipment/+/pressure",
        "equipment/+/vibration",
        "equipment/+/status"
    ]
    
    # Data Processing
    DATA_RETENTION_DAYS: int = 90
    BATCH_SIZE: int = 1000
    PROCESSING_INTERVAL_SECONDS: int = 30
    
    # Monitoring and Alerting
    ALERT_THRESHOLDS: dict = {
        "temperature": {"min": 0, "max": 100},
        "pressure": {"min": 0, "max": 50},
        "vibration": {"min": 0, "max": 10}
    }
    
    # Equipment Integration
    MAX_EQUIPMENT_CONNECTIONS: int = 15
    CONNECTION_TIMEOUT_SECONDS: int = 30
    HEARTBEAT_INTERVAL_SECONDS: int = 60
    
    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # File Storage
    DATA_EXPORT_PATH: str = "./data/exports"
    RAW_DATA_PATH: str = "./data/raw"
    PROCESSED_DATA_PATH: str = "./data/processed"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()