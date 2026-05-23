import asyncio
import json
import random
import time
from datetime import datetime, timedelta, timezone

import pytz
from aiogram import Bot
from loguru import logger
from redis.asyncio import Redis

from app.bot.texts import t
from app.config import settings
from app.core.encryption import decrypt
from app.db.engine import SessionFactory
from app.db.models import Applicant, AttemptOutcome, MonitoringTask, TaskStatus, User
from app.db.repository import (
    ApplicantRepository,
    BookingRepository,
    MonitoringTaskRepository,
    SlotAttemptRepository,
)
from app.monitor.otp_bridge import wait_for_otp
from app.prenotami.client import PrenotamiClient
from app.prenotami.exceptions import (
    AuthError,
    BookingConflict,
    CaptchaEncountered,
    NoSlotsAvailable,
    OtpTimeout,
    SessionExpired,
    SiteStructureChanged,
)
from app.prenotami.flows import (
    book_slot_and_confirm,
    find_first_slot,
    is_authenticated,
    login,
    open_belgrade_schengen_service,
)

ROME = pytz.timezone("Europe/Rome")


def _is_peak_window(now_utc: datetime) -> bool:
    now_rome = now_utc.astimezone(ROME)
    minute_of_day = now_rome.hour * 60 + now_rome.minute
    # 23:50 to 00:30 inclusive
    return minute_of_day >= 23 * 60 + 50 or minute_of_day <= 30


def _next_interval(now_utc: datetime) -> timedelta:
    base = settings.monitor_peak_interval_sec if _is_peak_window(now_utc) else settings.monitor_default_interval_sec
    jitter = random.uniform(-settings.monitor_jitter_sec, settings.monitor_jitter_sec)
    return timedelta(seconds=max(5, base + jitter))


async def run_loop(bot: Bot, redis: Redis) -> None:
    """Main worker loop: pick due tasks, run one check cycle per task, sleep."""
    logger.info("Monitor worker started")
    while True:
        try:
            await _tick(bot, redis)
        except Exception as e:
            logger.exception("Monitor tick failed: {}", e)
        await asyncio.sleep(5)


async def _tick(bot: Bot, redis: Redis) -> None:
    now = datetime.now(timezone.utc)
    async with SessionFactory() as session:
        tasks = await MonitoringTaskRepository(session).list_due(now)
        if not tasks:
            return
        for task in tasks:
            applicant = await session.get(Applicant, task.applicant_id)
            if applicant is None:
                continue
            user = await session.get(User, applicant.user_id)
            if user is None:
                continue
            await _check_task(session, bot, redis, task, applicant, user)


async def _check_task(
    session,
    bot: Bot,
    redis: Redis,
    task: MonitoringTask,
    applicant: Applicant,
    user: User,
) -> None:
    started = time.monotonic()
    repo_task = MonitoringTaskRepository(session)
    repo_attempt = SlotAttemptRepository(session)

    credentials = json.loads(decrypt(applicant.credentials_encrypted))
    next_at = datetime.now(timezone.utc) + _next_interval(datetime.now(timezone.utc))

    async def otp_provider() -> str | None:
        await bot.send_message(user.telegram_id, t(user.language, "otp_request", timeout=settings.otp_timeout_sec))
        code = await wait_for_otp(redis, task.id, timeout=settings.otp_timeout_sec)
        if code is None:
            await bot.send_message(user.telegram_id, t(user.language, "otp_timeout"))
        return code

    try:
        async with PrenotamiClient(applicant, session) as client:
            if not await is_authenticated(client):
                await login(client, email=credentials["email"], password=credentials["password"], otp_provider=otp_provider)

            await open_belgrade_schengen_service(client)

            slot = await find_first_slot(
                client,
                date_from=task.date_from.date(),
                date_to=task.date_to.date(),
                weekdays_mask=task.weekdays_mask,
            )

            await repo_attempt.log(
                task_id=task.id,
                outcome=AttemptOutcome.SLOT_FOUND.value,
                duration_ms=int((time.monotonic() - started) * 1000),
            )

            code, when = await book_slot_and_confirm(client, slot, otp_provider=otp_provider)

            await BookingRepository(session).create(
                task_id=task.id,
                prenotami_code=code,
                slot_datetime=when,
                raw_response_encrypted=None,
            )
            await repo_attempt.log(task_id=task.id, outcome=AttemptOutcome.BOOKED.value)
            await repo_task.set_status(task, TaskStatus.COMPLETED)
            task.next_check_at = None
            await session.flush()

            await bot.send_message(
                user.telegram_id,
                t(
                    user.language,
                    "booking_success",
                    slot=when.strftime("%Y-%m-%d %H:%M"),
                    code=code or "—",
                ),
            )
            return

    except NoSlotsAvailable:
        await repo_attempt.log(task_id=task.id, outcome=AttemptOutcome.NO_SLOTS.value)
    except AuthError as e:
        await repo_attempt.log(task_id=task.id, outcome=AttemptOutcome.AUTH_ERROR.value, error_text=str(e))
        await repo_task.set_status(task, TaskStatus.PAUSED)
        next_at = None
        await bot.send_message(user.telegram_id, t(user.language, "auth_error"))
    except OtpTimeout as e:
        await repo_attempt.log(task_id=task.id, outcome=AttemptOutcome.OTP_TIMEOUT.value, error_text=str(e))
    except CaptchaEncountered as e:
        await repo_attempt.log(task_id=task.id, outcome=AttemptOutcome.CAPTCHA.value, error_text=str(e))
        await repo_task.set_status(task, TaskStatus.PAUSED)
        next_at = None
        await bot.send_message(user.telegram_id, t(user.language, "captcha_alert"))
    except SessionExpired as e:
        await repo_attempt.log(task_id=task.id, outcome=AttemptOutcome.AUTH_ERROR.value, error_text=str(e))
    except SiteStructureChanged as e:
        await repo_attempt.log(task_id=task.id, outcome=AttemptOutcome.SITE_CHANGED.value, error_text=str(e))
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(admin_id, f"Site structure changed for task #{task.id}: {e}")
            except Exception:
                pass
    except BookingConflict as e:
        await repo_attempt.log(task_id=task.id, outcome=AttemptOutcome.NO_SLOTS.value, error_text=str(e))
    except Exception as e:
        logger.exception("Unhandled error in check: {}", e)
        await repo_attempt.log(task_id=task.id, outcome=AttemptOutcome.UNKNOWN_ERROR.value, error_text=str(e)[:1000])

    await repo_task.record_check(task, next_at)
