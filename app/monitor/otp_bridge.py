import asyncio

from loguru import logger
from redis.asyncio import Redis

from app.config import settings


def pending_request_key_for_task(task_id: int) -> str:
    return f"otp:request:{task_id}"


def response_channel_for_task(task_id: int) -> str:
    return f"otp:response:{task_id}"


async def open_otp_request(redis: Redis, task_id: int) -> None:
    await redis.set(pending_request_key_for_task(task_id), "1", ex=settings.otp_timeout_sec)


async def close_otp_request(redis: Redis, task_id: int) -> None:
    await redis.delete(pending_request_key_for_task(task_id))


async def publish_otp_response(redis: Redis, task_id: int, code: str) -> None:
    await redis.publish(response_channel_for_task(task_id), code)


async def wait_for_otp(redis: Redis, task_id: int, timeout: float | None = None) -> str | None:
    """Block until OTP response arrives or timeout. Returns code or None."""
    timeout = timeout if timeout is not None else float(settings.otp_timeout_sec)
    pubsub = redis.pubsub()
    await pubsub.subscribe(response_channel_for_task(task_id))
    try:
        await open_otp_request(redis, task_id)
        deadline = asyncio.get_event_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                logger.warning("OTP timed out for task {}", task_id)
                return None
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=min(remaining, 5.0))
            if message is None:
                continue
            data = message.get("data")
            if data is None:
                continue
            code = data.decode("utf-8") if isinstance(data, bytes) else str(data)
            return code
    finally:
        await pubsub.unsubscribe(response_channel_for_task(task_id))
        await pubsub.close()
        await close_otp_request(redis, task_id)
