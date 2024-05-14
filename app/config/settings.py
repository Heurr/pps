from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.constants import Entity, LogFormatType


class Settings(BaseSettings):
    APP_ENV: str
    IS_UNIT_TEST: bool = False

    # PostgreSQL database
    POSTGRES_DB_HOST: str
    POSTGRES_DB_USER: str = "api-user"
    POSTGRES_DB_NAME: str = "price-services"
    POSTGRES_DB_PASSWORD: str

    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379
    REDIS_USER: str = ""
    REDIS_PASSWORD: str = ""

    PROMETHEUS_PORT: int = 9090

    SENTRY_DSN: str | None = None

    @property
    def postgres_db_dsn(self) -> str:
        return "postgresql+asyncpg://{}:{}@{}/{}".format(
            self.POSTGRES_DB_USER,
            self.POSTGRES_DB_PASSWORD,
            self.POSTGRES_DB_HOST,
            self.POSTGRES_DB_NAME,
        )

    @property
    def redis_dsn(self) -> str:
        return f"redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV.lower() == "dev"

    model_config = SettingsConfigDict(env_prefix="PPS_")


class ApiSettings(Settings):
    APP_SECRET: str

    # Docs
    DOC_URL: str = "/-/docs"
    REDOC_URL: str = "/-/redoc"
    OPENAPI_URL: str = "/-/openapi.json"


class WorkerSetting(Settings):
    WORKER_BUFFER_SIZE: int = 100
    WORKER_POP_TIMEOUT: float = 0.2
    WORKER_MESSAGE_LOG_INTERVAL: int = 1000


class ServiceSettings(Settings):
    FORCE_ENTITY_UPDATE: bool = False


class LogSettings(BaseSettings):
    LOG_LEVEL: str = "info"
    LOG_FORMAT: LogFormatType = LogFormatType.DEFAULT

    model_config = SettingsConfigDict(env_prefix="PPS_")


class RabbitmqSettings(Settings):
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "op-od"
    RABBITMQ_PASSWORD: str
    RABBITMQ_VIRTUAL_HOST: str
    RABBITMQ_EXCHANGE_NAME: str
    RABBITMQ_PREFETCH_COUNT: int = 200
    RABBITMQ_ENTITY_SERVER_MAP: dict[Entity, dict] = {}

    def rabbitmq_dsn(self, entity: Entity | None = None) -> str:
        if entity is None:
            rmq_host = self.RABBITMQ_HOST
            rmq_port = self.RABBITMQ_PORT
        else:
            entity_server_settings = self.RABBITMQ_ENTITY_SERVER_MAP.get(entity, {})
            rmq_host = entity_server_settings.get("rmqHost", self.RABBITMQ_HOST)
            rmq_port = entity_server_settings.get("rmqPort", self.RABBITMQ_PORT)

        return "amqp://{}:{}@{}:{}/{}".format(
            self.RABBITMQ_USER,
            self.RABBITMQ_PASSWORD,
            rmq_host,
            rmq_port,
            self.RABBITMQ_VIRTUAL_HOST,
        )


class RepublishSettings(RabbitmqSettings):
    TARGET_ROUTING_KEY_MAP: dict[Entity, str]
    REPLY_TO_ROUTING_KEY: str
    REPUBLISH_TO_ROUTING_KEY_MAP: dict[Entity, str]
    USER_AGENT: str
    CONTENT_TYPE: str = "application/json"
    REPUBLISH_BATCH: int = 1000


class ProductPricePublishSettings(RabbitmqSettings):
    ROUTING_KEY: str = "op-product-price.v1.update"
    USER_AGENT: str = "Product Price Service Entity Publisher"
    CONTENT_TYPE: str = "application/json"


class ConsumerSettings(RabbitmqSettings):
    CONSUMER_RABBITMQ_QUEUE_MAPPING: dict[Entity, dict] = {}
    CONSUMER_RABBITMQ_CREATE_QUEUES: bool = False
    CONSUMER_RABBITMQ_ENTITIES: dict[Entity, Any] = {}
    CONSUMER_RABBITMQ_QUEUE_POSTFIX: str | None = None
    CONSUMER_MAX_DELAY: float = 1
    CONSUMER_REDIS_CAPACITY_THRESHOLD_IN_PERCENT: int = 95
    CONSUMER_ITERATOR_TIMEOUT: float = 1

    def rabbitmq_entity_queue_mapping(self, entity) -> dict:
        return self.CONSUMER_RABBITMQ_QUEUE_MAPPING.get(entity, {})

    def rabbitmq_exchange_name(self, entity: Entity | None = None) -> str:
        if entity is None:
            return self.RABBITMQ_EXCHANGE_NAME
        return self.rabbitmq_entity_queue_mapping(entity).get(
            "exchange", self.RABBITMQ_EXCHANGE_NAME
        )

    def rmq_max_delay(self, entity: Entity | None = None) -> float:
        if entity is None:
            return self.CONSUMER_MAX_DELAY
        return self.rabbitmq_entity_queue_mapping(entity).get(
            "maxDelay", self.CONSUMER_MAX_DELAY
        )

    def filtered_countries(self, entity: Entity | None) -> list[str]:
        if not entity:
            return []

        return self.CONSUMER_RABBITMQ_ENTITIES.get(entity, {}).get(
            "filteredCountries", []
        )


class EntityPopulationJobSettings(Settings):
    BATCH_SIZE: int = 1000
    EXPIRE_TIME: int = 6 * 60 * 60  # 6 hours in seconds


class MaintenanceJobSettings(Settings):
    HISTORY_INTERVAL_IN_DAYS: int
    PARTITIONS_AHEAD: int
    PARTITIONS_FILL_FACTOR: int


class JobSettings(Settings):
    JOB_BATCH_SIZE: int = 200
    JOB_QUEUE_POP_TIMEOUT: float = 0.2


base_settings = Settings()
