from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from app.api.v1 import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.services.protocols.mqtt.client import MQTTService
from app.services.protocols.opc_ua.client import OPCUAService
from app.database.connection import init_db

# Initialize logging
setup_logging()

# Background services
mqtt_service = MQTTService()
opcua_service = OPCUAService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events"""
    # Startup
    await init_db()
    await mqtt_service.connect()
    await opcua_service.connect()
    
    yield
    
    # Shutdown
    await mqtt_service.disconnect()
    await opcua_service.disconnect()

# Create FastAPI application
app = FastAPI(
    title="Digital Twin Data Integration Platform",
    description="RESTful APIs for unified industrial equipment data integration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimiterMiddleware)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return JSONResponse({
        "message": "Digital Twin Data Integration Platform API",
        "version": "1.0.0",
        "status": "active",
        "protocols": ["OPC UA", "MQTT", "REST"]
    })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "services": {
            "mqtt": mqtt_service.is_connected,
            "opc_ua": opcua_service.is_connected,
            "database": True  # Add actual DB health check
        }
    })

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )