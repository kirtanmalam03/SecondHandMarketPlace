# Routes package initialization
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.chat_routes import chat_bp

__all__ = ["auth_bp", "product_bp", "chat_bp"]