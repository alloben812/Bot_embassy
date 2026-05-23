from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.texts import t
from app.db.models import TaskStatus
from app.db.repository import (
    ApplicantRepository,
    MonitoringTaskRepository,
    UserRepository,
)

router = Router(name="monitor")


@router.message(Command("start_monitor"))
async def cmd_start_monitor(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    applicant = await ApplicantRepository(session).get_for_user(user.id)
    if applicant is None:
        await message.answer(t(user.language, "monitor_no_data"))
        return

    repo = MonitoringTaskRepository(session)
    task = await repo.get_active_for_applicant(applicant.id)
    if task is None:
        await message.answer(t(user.language, "monitor_no_data"))
        return

    if task.status == TaskStatus.ACTIVE.value:
        await message.answer(t(user.language, "monitor_already_running"))
        return

    await repo.set_status(task, TaskStatus.ACTIVE)
    task.next_check_at = datetime.now(timezone.utc)
    await session.flush()
    await message.answer(t(user.language, "monitor_started"))


@router.message(Command("pause"))
async def cmd_pause(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    applicant = await ApplicantRepository(session).get_for_user(user.id)
    if applicant is None:
        await message.answer(t(user.language, "monitor_no_data"))
        return
    repo = MonitoringTaskRepository(session)
    task = await repo.get_active_for_applicant(applicant.id)
    if task is None:
        await message.answer(t(user.language, "monitor_no_data"))
        return
    await repo.set_status(task, TaskStatus.PAUSED)
    await message.answer(t(user.language, "monitor_paused"))


@router.message(Command("stop"))
async def cmd_stop(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    applicant = await ApplicantRepository(session).get_for_user(user.id)
    if applicant is None:
        await message.answer(t(user.language, "monitor_no_data"))
        return
    await session.delete(applicant)
    await session.flush()
    await message.answer(t(user.language, "monitor_stopped"))


@router.message(Command("status"))
async def cmd_status(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    applicant = await ApplicantRepository(session).get_for_user(user.id)
    if applicant is None:
        await message.answer(t(user.language, "monitor_no_data"))
        return
    task = await MonitoringTaskRepository(session).get_active_for_applicant(applicant.id)
    if task is None:
        await message.answer(t(user.language, "monitor_no_data"))
        return

    await message.answer(
        t(
            user.language,
            "status_template",
            task_id=task.id,
            status=task.status,
            date_from=task.date_from.date().isoformat(),
            date_to=task.date_to.date().isoformat(),
            last_check=task.last_check_at.strftime("%Y-%m-%d %H:%M:%S UTC") if task.last_check_at else "-",
            next_check=task.next_check_at.strftime("%Y-%m-%d %H:%M:%S UTC") if task.next_check_at else "-",
            attempts=task.attempts_count,
        )
    )
