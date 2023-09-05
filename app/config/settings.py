from pydantic import BaseSettings

from app.constants import LogFormatType


class Settings(BaseSettings):
    APP_ENV: str
    IS_UNIT_TEST: bool = False

    # PostgreSQL database
    POSTGRES_DB_HOST: str
    POSTGRES_DB_USER: str = "api-user"
    POSTGRES_DB_NAME: str = "price-services"
    POSTGRES_DB_PASSWORD: str

    PROMETHEUS_PORT: int = 9090

    SENTRY_DSN: str | None = None

    @property
    def postgres_db_dsn(self) -> str:
        return "postgresql+asyncpg://{}:{}@{}/{}".format(  # pylint: disable=consider-using-f-string
            self.POSTGRES_DB_USER,
            self.POSTGRES_DB_PASSWORD,
            self.POSTGRES_DB_HOST,
            self.POSTGRES_DB_NAME,
        )

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV.lower() == "dev"

    class Config:
        env_prefix = "PS_"


class ApiSettings(Settings):
    APP_SECRET: str

    # Docs
    DOC_URL: str = "/-/docs"
    REDOC_URL: str = "/-/redoc"
    OPENAPI_URL: str = "/-/openapi.json"


class LogSettings(BaseSettings):
    LOG_LEVEL: str = "info"
    LOG_FORMAT: LogFormatType = LogFormatType.DEFAULT

    class Config:
        env_prefix = "PS_"


base_settings = Settings()
