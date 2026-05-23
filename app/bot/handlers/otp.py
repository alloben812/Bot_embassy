import re

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.texts import t
from app.db.repository import ApplicantRepository, MonitoringTaskRepository, UserRepository
from app.monitor.otp_bridge import pending_request_key_for_task, publish_otp_response

router = Router(name="otp")

OTP_RE = re.compile(r"^\s*(\d{6})\s*$")


@router.message(StateFilter(None), F.text.regexp(r"^\s*\d{4,8}\s*$"))
async def maybe_otp(message: Message, session: AsyncSession, redis: Redis) -> None:
    if message.from_user is None or message.text is None:
        return

    user = await UserRepository(session).get_or_create(message.from_user.id)
    applicant = await ApplicantRepository(session).get_for_user(user.id)
    if applicant is None:
        return
    task = await MonitoringTaskRepository(session).get_active_for_applicant(applicant.id)
    if task is None:
        return

    pending = await redis.get(pending_request_key_for_task(task.id))
    if pending is None:
        await message.answer(t(user.language, "otp_no_request"))
        return

    m = OTP_RE.match(message.text)
    if m is None:
        await message.answer(t(user.language, "otp_invalid"))
        return

    code = m.group(1)
    await publish_otp_response(redis, task.id, code)
    try:
        await message.delete()
    except Exception:
        pass
    await message.answer(t(user.language, "otp_received"))
