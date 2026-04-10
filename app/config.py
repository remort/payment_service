from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/payments"

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    RABBITMQ_MESSAGE_TTL_MSEC: int = 60000
    RABBITMQ_MESSAGE_RETRIES: int = 3
    PAYMENTS_QUEUE: str = "payments.new"
    PAYMENTS_RETENTION: str = "payments.retention"
    PAYMENTS_DLX: str = "payments.dlx"
    PAYMENTS_DLQ: str = "payments.dlq"

    API_KEY: str = "test-api-key-12345"

    OUTBOX_POLL_INTERVAL_SECONDS: int = 1

    class Config:
        env_file = ".env"


settings = Settings()

RABBITMQ_QUEUE_ARGUMENTS = {
    "x-dead-letter-exchange": settings.PAYMENTS_DLX,
    "x-dead-letter-routing-key": settings.PAYMENTS_DLQ,
    "x-message-ttl": settings.RABBITMQ_MESSAGE_TTL_MSEC,
    "x-max-retries": settings.RABBITMQ_MESSAGE_RETRIES,
}
