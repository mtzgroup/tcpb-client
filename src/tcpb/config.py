from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Base Settings configuration.

    Do not instantiate directly, use settings object on module
    """

    tcpb_host: str = "127.0.0.1"
    tcpb_port: int = 11111
    tcpb_frontend_host: str = "127.0.0.1"
    tcpb_frontend_port: int = 8080


settings = Settings()
