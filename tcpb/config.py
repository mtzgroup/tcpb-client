from pydantic import BaseSettings


class Settings(BaseSettings):
    """Base Settings configuration.

    Do not instantiate directly, use settings object on module
    """

    extras_qcvars_kwarg: str = "qcvars"
    extras_job_kwarg: str = "job_extras"
    tcfe_config_kwarg: str = "tcfe:config"


settings = Settings()
