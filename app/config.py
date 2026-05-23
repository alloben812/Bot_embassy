from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(..., alias="BOT_TOKEN")
    postgres_url: str = Field(..., alias="POSTGRES_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    bot_encryption_key: str = Field(..., alias="BOT_ENCRYPTION_KEY")

    log_level: str = Field("INFO", alias="LOG_LEVEL")
    sentry_dsn: str = Field("", alias="SENTRY_DSN")

    playwright_headless: bool = Field(True, alias="PLAYWRIGHT_HEADLESS")
    playwright_proxy_url: str = Field("", alias="PLAYWRIGHT_PROXY_URL")

    monitor_default_interval_sec: int = Field(90, alias="MONITOR_DEFAULT_INTERVAL_SEC")
    monitor_peak_interval_sec: int = Field(15, alias="MONITOR_PEAK_INTERVAL_SEC")
    monitor_jitter_sec: int = Field(30, alias="MONITOR_JITTER_SEC")
    otp_timeout_sec: int = Field(90, alias="OTP_TIMEOUT_SEC")

    admin_telegram_ids: str = Field("", alias="ADMIN_TELEGRAM_IDS")

    prenotami_base_url: str = Field("https://prenotami.esteri.it", alias="PRENOTAMI_BASE_URL")
    embassy_name: str = Field("Belgrado", alias="EMBASSY_NAME")

    @property
    def admin_ids(self) -> list[int]:
        if not self.admin_telegram_ids:
            return []
        return [int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip()]


settings = Settings()  # type: ignore[call-arg]
