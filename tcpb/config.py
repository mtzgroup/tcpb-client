from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Base Settings configuration.

    Do not instantiate directly, use settings object on module
    """

    tcfe_extras: str = "tcfe"
    tcfe_keywords: str = "tcfe:keywords"


settings = Settings()
