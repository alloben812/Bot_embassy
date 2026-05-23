import json
import re
from datetime import datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import (
    confirm_keyboard,
    serbia_status_keyboard,
    weekdays_keyboard,
)
from app.bot.states.registration import Registration
from app.bot.texts import t
from app.core.encryption import encrypt, encrypt_optional
from app.db.repository import ApplicantRepository, MonitoringTaskRepository, UserRepository

router = Router(name="register")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.message(Command("register"))
async def cmd_register(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    if user.accepted_disclaimer_at is None:
        await message.answer(t(user.language, "register_need_disclaimer"))
        return

    existing = await ApplicantRepository(session).get_for_user(user.id)
    if existing is not None:
        await message.answer(t(user.language, "register_already"))
        return

    await state.clear()
    await state.set_state(Registration.email)
    await message.answer(t(user.language, "register_start"))


@router.message(Registration.email)
async def step_email(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text is None or message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    email = message.text.strip()
    if not EMAIL_RE.match(email):
        await message.answer(t(user.language, "register_invalid_email"))
        return
    await state.update_data(email=email)
    await state.set_state(Registration.password)
    await message.answer(t(user.language, "register_password"))


@router.message(Registration.password)
async def step_password(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text is None or message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    await state.update_data(password=message.text)
    try:
        await message.delete()
    except Exception:
        pass
    await state.set_state(Registration.full_name)
    await message.answer(t(user.language, "register_full_name"))


@router.message(Registration.full_name)
async def step_full_name(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text is None or message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    await state.update_data(full_name=message.text.strip())
    await state.set_state(Registration.passport)
    await message.answer(t(user.language, "register_passport"))


@router.message(Registration.passport)
async def step_passport(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text is None or message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    await state.update_data(passport=message.text.strip().upper())
    await state.set_state(Registration.birth)
    await message.answer(t(user.language, "register_birth"))


@router.message(Registration.birth)
async def step_birth(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text is None or message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    parsed = _parse_date(message.text.strip())
    if parsed is None:
        await message.answer(t(user.language, "register_invalid_date"))
        return
    await state.update_data(birth=parsed.isoformat())
    await state.set_state(Registration.citizenship)
    await message.answer(t(user.language, "register_citizenship"))


@router.message(Registration.citizenship)
async def step_citizenship(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text is None or message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    await state.update_data(citizenship=message.text.strip().upper()[:3])
    await state.set_state(Registration.serbia_status)
    await message.answer(
        t(user.language, "register_serbia_status"),
        reply_markup=serbia_status_keyboard(user.language),
    )


@router.callback_query(Registration.serbia_status, F.data.startswith("status:"))
async def step_serbia_status(call: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if call.from_user is None or call.message is None or call.data is None:
        return
    status_type = call.data.split(":", 1)[1]
    await state.update_data(serbia_status_type=status_type)
    user = await UserRepository(session).get_or_create(call.from_user.id)
    await state.set_state(Registration.serbia_id)
    await call.message.answer(t(user.language, "register_serbia_id"))
    await call.answer()


@router.message(Registration.serbia_id)
async def step_serbia_id(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text is None or message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    await state.update_data(serbia_id=message.text.strip())
    await state.set_state(Registration.date_from)
    await message.answer(t(user.language, "register_date_from"))


@router.message(Registration.date_from)
async def step_date_from(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text is None or message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    parsed = _parse_date(message.text.strip())
    if parsed is None:
        await message.answer(t(user.language, "register_invalid_date"))
        return
    await state.update_data(date_from=parsed.isoformat())
    await state.set_state(Registration.date_to)
    await message.answer(t(user.language, "register_date_to"))


@router.message(Registration.date_to)
async def step_date_to(message: Message, session: AsyncSession, state: FSMContext) -> None:
    if message.text is None or message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id)
    parsed = _parse_date(message.text.strip())
    if parsed is None:
        await message.answer(t(user.language, "register_invalid_date"))
        return

    data = await state.get_data()
    date_from = datetime.fromisoformat(data["date_from"]).date()
    if parsed <= date_from or parsed > date_from + timedelta(days=185):
        await message.answer(t(user.language, "register_date_range_invalid"))
        return

    await state.update_data(date_to=parsed.isoformat(), weekdays_mask=0b1111111)
    await state.set_state(Registration.weekdays)
    await message.answer(
        t(user.language, "register_weekdays"),
        reply_markup=weekdays_keyboard(user.language, 0b1111111),
    )


@router.callback_query(Registration.weekdays, F.data.startswith("wd:"))
async def step_weekdays(call: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if call.from_user is None or call.message is None or call.data is None:
        return
    user = await UserRepository(session).get_or_create(call.from_user.id)
    payload = call.data.split(":", 1)[1]
    data = await state.get_data()
    mask: int = data.get("weekdays_mask", 0b1111111)

    if payload == "done":
        if mask == 0:
            await call.answer("Choose at least one day" if user.language == "en" else "Выберите хотя бы один день", show_alert=True)
            return
        await state.set_state(Registration.confirm)
        await call.message.answer(
            t(user.language, "register_summary", summary=_summary(data, mask, user.language)),
            reply_markup=confirm_keyboard(user.language),
        )
        await call.answer()
        return

    try:
        idx = int(payload)
    except ValueError:
        await call.answer()
        return
    mask ^= 1 << idx
    await state.update_data(weekdays_mask=mask)
    try:
        await call.message.edit_reply_markup(reply_markup=weekdays_keyboard(user.language, mask))
    except Exception:
        pass
    await call.answer()


@router.callback_query(Registration.confirm, F.data == "reg:cancel")
async def step_cancel(call: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if call.from_user is None or call.message is None:
        return
    user = await UserRepository(session).get_or_create(call.from_user.id)
    await state.clear()
    await call.message.answer(t(user.language, "register_cancelled"))
    await call.answer()


@router.callback_query(Registration.confirm, F.data == "reg:save")
async def step_save(call: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    if call.from_user is None or call.message is None:
        return
    user = await UserRepository(session).get_or_create(call.from_user.id)
    data = await state.get_data()

    credentials_payload = json.dumps({"email": data["email"], "password": data["password"]})
    profile_payload = json.dumps(
        {
            "full_name": data["full_name"],
            "passport": data["passport"],
            "birth": data["birth"],
            "citizenship": data["citizenship"],
        }
    )

    applicant = await ApplicantRepository(session).create(
        user_id=user.id,
        credentials_encrypted=encrypt(credentials_payload),
        profile_encrypted=encrypt(profile_payload),
        serbia_status_type=data["serbia_status_type"],
        serbia_status_id_encrypted=encrypt_optional(data.get("serbia_id")),
    )

    date_from = datetime.fromisoformat(data["date_from"]).replace(tzinfo=timezone.utc)
    date_to = datetime.fromisoformat(data["date_to"]).replace(tzinfo=timezone.utc)

    await MonitoringTaskRepository(session).create(
        applicant_id=applicant.id,
        date_from=date_from,
        date_to=date_to,
        weekdays_mask=data.get("weekdays_mask", 0b1111111),
    )

    await state.clear()
    await call.message.answer(t(user.language, "register_saved"))
    await call.answer()


def _parse_date(text: str):
    try:
        return datetime.strptime(text, "%d.%m.%Y").date()
    except ValueError:
        return None


def _summary(data: dict, mask: int, language: str) -> str:
    names_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    names = names_ru if language == "ru" else names_en
    selected = [n for i, n in enumerate(names) if mask & (1 << i)]
    return (
        f"email: {data['email']}\n"
        f"full_name: {data['full_name']}\n"
        f"passport: {data['passport']}\n"
        f"birth: {data['birth']}\n"
        f"citizenship: {data['citizenship']}\n"
        f"serbia_status: {data['serbia_status_type']} / {data.get('serbia_id', '-')}\n"
        f"date_from: {data['date_from']}\n"
        f"date_to: {data['date_to']}\n"
        f"weekdays: {', '.join(selected)}"
    )
