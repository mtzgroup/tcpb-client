from enum import Enum

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Base Settings configuration.

    Do not instantiate directly, use settings object on module
    """

    extras_qcvars_kwarg: str = "qcvars"
    extras_job_kwarg: str = "job_extras"
    tcfe_keywords: str = "tcfe:keywords"
    tcfe_config_native_files: str = "native_files"


settings = Settings()


class TCFEKeywords(str, Enum):
    """Supported keywords for the TCFrontEndClient"""

    c0 = "c0"
    ca0 = "ca0"
    cb0 = "cb0"
    scratch_messy = "scratch_messy"
    uploads_messy = "uploads_messy"
    native_files = "native_files"
