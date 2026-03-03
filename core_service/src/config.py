from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    database_url: str
    redis_url: str

    monitor_scan_minutes_min: int = 30
    monitor_scan_minutes_max: int = 60
    mutual_jitter_min_seconds: int = 30
    mutual_jitter_max_seconds: int = 60

    dynamic_limit_initial: int = 80
    dynamic_limit_min: int = 40
    dynamic_limit_max: int = 150

    cooldown_min_minutes: int = 10
    cooldown_max_minutes: int = 30

    telethon_mode: str = 'mock'  # mock | live

    worker_tick_seconds: int = Field(default=5, ge=1)
