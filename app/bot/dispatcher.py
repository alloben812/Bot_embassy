from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app.bot.handlers import monitor, otp, register, start
from app.bot.middlewares.db import DBSessionMiddleware
from app.config import settings


def build_bot() -> Bot:
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def build_dispatcher(redis: Redis) -> Dispatcher:
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DBSessionMiddleware())

    async def inject_redis(handler, event, data):
        data["redis"] = redis
        return await handler(event, data)

    dp.update.middleware(inject_redis)

    dp.include_router(start.router)
    dp.include_router(register.router)
    dp.include_router(monitor.router)
    dp.include_router(otp.router)
    return dp
