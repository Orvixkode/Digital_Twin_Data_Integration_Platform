from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
import asyncio
from app.core.config import settings

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to protect API endpoints"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)
        self.window_size = 60  # 1 minute window
        self.max_requests = settings.RATE_LIMIT_PER_MINUTE
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        self._cleanup_old_requests(client_ip, current_time)
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate Limit Exceeded",
                    "message": f"Maximum {self.max_requests} requests per minute allowed",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Record this request
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        
        # Add rate limiting headers
        remaining = max(0, self.max_requests - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self, client_ip: str, current_time: float):
        """Remove requests outside the time window"""
        cutoff_time = current_time - self.window_size
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff_time
        ]