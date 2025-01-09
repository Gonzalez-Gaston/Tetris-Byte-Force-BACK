from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.services.auth_service import AuthService

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_service = AuthService()

    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization")
        if token:
            token = token.replace("Bearer ", "")
            try:
                user = await self.auth_service.get_current_user(token)
                request.state.user = user
            except Exception as e:
                return JSONResponse({"error": "Invalid token"}, status_code=401)
        else:
            request.state.user = None
        response = await call_next(request)
        return response