import asyncio

from loguru import logger
from redis.asyncio import Redis

from app.bot.dispatcher import build_bot, build_dispatcher
from app.config import settings
from app.core.logger import setup_logging


async def main() -> None:
    setup_logging()
    bot = build_bot()
    redis = Redis.from_url(settings.redis_url)
    dp = build_dispatcher(redis)

    logger.info("Starting Telegram bot")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await redis.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
