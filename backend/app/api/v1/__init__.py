from fastapi import APIRouter
from .endpoints import equipment, sensors, data, monitoring, integration

router = APIRouter()

# Include all endpoint routers
router.include_router(equipment.router, prefix="/equipment", tags=["equipment"])
router.include_router(sensors.router, prefix="/sensors", tags=["sensors"])  
router.include_router(data.router, prefix="/data", tags=["data-processing"])
router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
router.include_router(integration.router, prefix="/integration", tags=["integration"])