"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False, server_default="ru"),
        sa.Column("accepted_disclaimer_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "applicants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("credentials_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("profile_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("serbia_status_type", sa.String(length=32), nullable=False),
        sa.Column("serbia_status_id_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_applicants_user_id", "applicants", ["user_id"])

    op.create_table(
        "monitoring_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("date_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("date_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("weekdays_mask", sa.Integer(), nullable=False, server_default="127"),
        sa.Column("last_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_monitoring_tasks_applicant_id", "monitoring_tasks", ["applicant_id"])
    op.create_index("ix_monitoring_tasks_status", "monitoring_tasks", ["status"])
    op.create_index("ix_monitoring_tasks_next_check_at", "monitoring_tasks", ["next_check_at"])

    op.create_table(
        "slot_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("monitoring_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
    )
    op.create_index("ix_slot_attempts_task_id", "slot_attempts", ["task_id"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("monitoring_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prenotami_code", sa.String(length=64), nullable=True),
        sa.Column("slot_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_response_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("notified_user", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_bookings_task_id", "bookings", ["task_id"])

    op.create_table(
        "prenotami_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("applicant_id", sa.Integer(), sa.ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state_json_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("applicant_id"),
    )


def downgrade() -> None:
    op.drop_table("prenotami_sessions")
    op.drop_index("ix_bookings_task_id", table_name="bookings")
    op.drop_table("bookings")
    op.drop_index("ix_slot_attempts_task_id", table_name="slot_attempts")
    op.drop_table("slot_attempts")
    op.drop_index("ix_monitoring_tasks_next_check_at", table_name="monitoring_tasks")
    op.drop_index("ix_monitoring_tasks_status", table_name="monitoring_tasks")
    op.drop_index("ix_monitoring_tasks_applicant_id", table_name="monitoring_tasks")
    op.drop_table("monitoring_tasks")
    op.drop_index("ix_applicants_user_id", table_name="applicants")
    op.drop_table("applicants")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
