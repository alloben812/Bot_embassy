from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Applicant,
    Booking,
    MonitoringTask,
    PrenotamiSession,
    SlotAttempt,
    TaskStatus,
    User,
)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_or_create(self, telegram_id: int, language: str = "ru") -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(telegram_id=telegram_id, language=language)
            self.session.add(user)
            await self.session.flush()
        return user

    async def accept_disclaimer(self, user: User) -> None:
        user.accepted_disclaimer_at = datetime.now(timezone.utc)
        await self.session.flush()


class ApplicantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, user_id: int) -> Applicant | None:
        result = await self.session.execute(select(Applicant).where(Applicant.user_id == user_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: int,
        credentials_encrypted: bytes,
        profile_encrypted: bytes,
        serbia_status_type: str,
        serbia_status_id_encrypted: bytes | None,
    ) -> Applicant:
        applicant = Applicant(
            user_id=user_id,
            credentials_encrypted=credentials_encrypted,
            profile_encrypted=profile_encrypted,
            serbia_status_type=serbia_status_type,
            serbia_status_id_encrypted=serbia_status_id_encrypted,
        )
        self.session.add(applicant)
        await self.session.flush()
        return applicant


class MonitoringTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, task_id: int) -> MonitoringTask | None:
        return await self.session.get(MonitoringTask, task_id)

    async def get_active_for_applicant(self, applicant_id: int) -> MonitoringTask | None:
        result = await self.session.execute(
            select(MonitoringTask).where(
                MonitoringTask.applicant_id == applicant_id,
                MonitoringTask.status.in_([TaskStatus.PENDING.value, TaskStatus.ACTIVE.value, TaskStatus.PAUSED.value]),
            )
        )
        return result.scalar_one_or_none()

    async def list_due(self, now: datetime) -> list[MonitoringTask]:
        result = await self.session.execute(
            select(MonitoringTask).where(
                MonitoringTask.status == TaskStatus.ACTIVE.value,
                (MonitoringTask.next_check_at.is_(None)) | (MonitoringTask.next_check_at <= now),
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        applicant_id: int,
        date_from: datetime,
        date_to: datetime,
        weekdays_mask: int,
    ) -> MonitoringTask:
        task = MonitoringTask(
            applicant_id=applicant_id,
            date_from=date_from,
            date_to=date_to,
            weekdays_mask=weekdays_mask,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def set_status(self, task: MonitoringTask, status: TaskStatus) -> None:
        task.status = status.value
        await self.session.flush()

    async def record_check(self, task: MonitoringTask, next_check_at: datetime | None) -> None:
        task.last_check_at = datetime.now(timezone.utc)
        task.next_check_at = next_check_at
        task.attempts_count += 1
        await self.session.flush()


class SlotAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        *,
        task_id: int,
        outcome: str,
        error_text: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        self.session.add(
            SlotAttempt(task_id=task_id, outcome=outcome, error_text=error_text, duration_ms=duration_ms)
        )
        await self.session.flush()


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        task_id: int,
        prenotami_code: str | None,
        slot_datetime: datetime,
        raw_response_encrypted: bytes | None,
    ) -> Booking:
        booking = Booking(
            task_id=task_id,
            prenotami_code=prenotami_code,
            slot_datetime=slot_datetime,
            raw_response_encrypted=raw_response_encrypted,
        )
        self.session.add(booking)
        await self.session.flush()
        return booking

    async def mark_notified(self, booking: Booking) -> None:
        booking.notified_user = True
        await self.session.flush()


class PrenotamiSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, applicant_id: int) -> PrenotamiSession | None:
        result = await self.session.execute(
            select(PrenotamiSession).where(PrenotamiSession.applicant_id == applicant_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        applicant_id: int,
        state_json_encrypted: bytes,
        expires_at: datetime | None,
    ) -> PrenotamiSession:
        existing = await self.get(applicant_id)
        if existing:
            existing.state_json_encrypted = state_json_encrypted
            existing.expires_at = expires_at
            await self.session.flush()
            return existing
        new_session = PrenotamiSession(
            applicant_id=applicant_id,
            state_json_encrypted=state_json_encrypted,
            expires_at=expires_at,
        )
        self.session.add(new_session)
        await self.session.flush()
        return new_session

    async def invalidate(self, applicant_id: int) -> None:
        existing = await self.get(applicant_id)
        if existing:
            await self.session.delete(existing)
            await self.session.flush()
