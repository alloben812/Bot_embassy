import asyncio

from loguru import logger
from redis.asyncio import Redis

from app.bot.dispatcher import build_bot
from app.config import settings
from app.core.logger import setup_logging
from app.monitor.worker import run_loop


async def main() -> None:
    setup_logging()
    bot = build_bot()
    redis = Redis.from_url(settings.redis_url)
    logger.info("Starting monitor worker")
    try:
        await run_loop(bot, redis)
    finally:
        await redis.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
