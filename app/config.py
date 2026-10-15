from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    database_url: str = "postgresql+asyncpg://polsia:polsia_secret_2026@postgres:5432/polsia"
    api_key: str = "polsia-nfc-dev-key-2026"
    sandbox_mode: bool = True
    claude_cli_path: str = "/usr/local/bin/claude"
    claude_cli_mock: bool = False          # env: CLAUDE_CLI_MOCK
    claude_cli_mock_response: str = '{"result": "Mock response"}'  # env: CLAUDE_CLI_MOCK_RESPONSE
    morning_cycle_hour: int = 10           # env: MORNING_CYCLE_HOUR
    evening_cycle_hour: int = 20           # env: EVENING_CYCLE_HOUR
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    redis_url: str = "redis://redis:6379/0"
    chroma_persist_dir: str = "/app/data/chroma"
    stripe_webhook_secret: str = ""
    timezone: str = "Asia/Kolkata"


settings = Settings()
