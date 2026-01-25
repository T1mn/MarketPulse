"""API 模块"""
from .app import app
from .routes import chatbot, health, admin

__all__ = ["app"]
