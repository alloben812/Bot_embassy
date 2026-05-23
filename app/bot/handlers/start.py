from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.common import disclaimer_keyboard
from app.bot.texts import t
from app.db.repository import UserRepository

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    repo = UserRepository(session)
    user = await repo.get_or_create(message.from_user.id, language=_detect_language(message))

    await message.answer(t(user.language, "welcome"))
    await message.answer(
        f"{t(user.language, 'disclaimer_title')}\n\n{t(user.language, 'disclaimer_body')}",
        reply_markup=disclaimer_keyboard(user.language, residency_ok=False, risks_ok=False),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user = await UserRepository(session).get_or_create(message.from_user.id, language=_detect_language(message))
    await message.answer(t(user.language, "help"))


@router.callback_query(F.data.startswith("disc:"))
async def disclaimer_callback(call: CallbackQuery, session: AsyncSession) -> None:
    if call.from_user is None or call.message is None or call.data is None:
        return
    action = call.data.split(":", 1)[1]
    repo = UserRepository(session)
    user = await repo.get_or_create(call.from_user.id)

    state_key = f"disc_state:{call.from_user.id}"
    state = _DISCLAIMER_STATE.setdefault(state_key, {"residency": False, "risks": False})

    if action == "residency":
        state["residency"] = True
    elif action == "risks":
        state["risks"] = True
    elif action == "accept":
        if state["residency"] and state["risks"]:
            await repo.accept_disclaimer(user)
            await call.message.edit_text(t(user.language, "disclaimer_accepted"))
            _DISCLAIMER_STATE.pop(state_key, None)
            await call.answer()
            return
        else:
            await call.answer(t(user.language, "disclaimer_required"), show_alert=True)
            return

    try:
        await call.message.edit_reply_markup(
            reply_markup=disclaimer_keyboard(user.language, state["residency"], state["risks"])
        )
    except Exception:
        pass
    await call.answer()


_DISCLAIMER_STATE: dict[str, dict[str, bool]] = {}


def _detect_language(message: Message) -> str:
    if message.from_user and message.from_user.language_code:
        return "ru" if message.from_user.language_code.startswith("ru") else "en"
    return "ru"
