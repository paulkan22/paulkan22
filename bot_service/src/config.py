from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    bot_token: str
    bot_whitelist: str
    database_url: str
    redis_url: str

    @field_validator('bot_whitelist')
    @classmethod
    def validate_whitelist(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('BOT_WHITELIST must contain at least one user id')
        return value

    def whitelist_ids(self) -> set[int]:
        return {int(item.strip()) for item in self.bot_whitelist.split(',') if item.strip()}
