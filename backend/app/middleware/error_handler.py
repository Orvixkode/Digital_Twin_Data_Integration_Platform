from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        
        except HTTPException as e:
            # Let FastAPI handle HTTP exceptions normally
            raise e
        
        except Exception as e:
            # Log the error
            logger.error(f"Unhandled exception: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return structured error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred in the Digital Twin platform",
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path),
                    "method": request.method
                }
            )