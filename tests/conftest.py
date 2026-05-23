import os

os.environ.setdefault("BOT_TOKEN", "test:test")
os.environ.setdefault("POSTGRES_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from cryptography.fernet import Fernet  # noqa: E402

os.environ.setdefault("BOT_ENCRYPTION_KEY", Fernet.generate_key().decode())
