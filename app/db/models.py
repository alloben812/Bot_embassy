from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TaskStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class AttemptOutcome(StrEnum):
    NO_SLOTS = "no_slots"
    SLOT_FOUND = "slot_found"
    BOOKED = "booked"
    AUTH_ERROR = "auth_error"
    CAPTCHA = "captcha"
    OTP_TIMEOUT = "otp_timeout"
    SITE_CHANGED = "site_changed"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class SerbiaStatusType(StrEnum):
    BORAVAK_TEMPORARY = "boravak_temporary"
    BORAVAK_PERMANENT = "boravak_permanent"
    SERBIA_C_VISA = "serbia_c_visa"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(8), default="ru", nullable=False)
    accepted_disclaimer_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    applicants: Mapped[list["Applicant"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Applicant(Base):
    __tablename__ = "applicants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    credentials_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    profile_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    serbia_status_type: Mapped[str] = mapped_column(String(32), nullable=False)
    serbia_status_id_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="applicants")
    tasks: Mapped[list["MonitoringTask"]] = relationship(back_populates="applicant", cascade="all, delete-orphan")
    sessions: Mapped[list["PrenotamiSession"]] = relationship(
        back_populates="applicant", cascade="all, delete-orphan"
    )


class MonitoringTask(Base):
    __tablename__ = "monitoring_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    applicant_id: Mapped[int] = mapped_column(
        ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(String(16), default=TaskStatus.PENDING.value, nullable=False, index=True)
    date_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    weekdays_mask: Mapped[int] = mapped_column(Integer, default=0b1111111, nullable=False)

    last_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    attempts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    applicant: Mapped[Applicant] = relationship(back_populates="tasks")
    attempts: Mapped[list["SlotAttempt"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class SlotAttempt(Base):
    __tablename__ = "slot_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("monitoring_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    error_text: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    task: Mapped[MonitoringTask] = relationship(back_populates="attempts")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("monitoring_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prenotami_code: Mapped[str | None] = mapped_column(String(64))
    slot_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_response_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    notified_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    task: Mapped[MonitoringTask] = relationship(back_populates="bookings")


class PrenotamiSession(Base):
    __tablename__ = "prenotami_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    applicant_id: Mapped[int] = mapped_column(
        ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    state_json_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    applicant: Mapped[Applicant] = relationship(back_populates="sessions")
