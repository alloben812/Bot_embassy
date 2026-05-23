from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.texts import t

WEEKDAY_KEYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
WEEKDAY_KEYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def disclaimer_keyboard(language: str, residency_ok: bool, risks_ok: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=t(language, "btn_confirm_residency_done" if residency_ok else "btn_confirm_residency"),
                callback_data="disc:residency",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "btn_confirm_risks_done" if risks_ok else "btn_confirm_risks"),
                callback_data="disc:risks",
            )
        ],
    ]
    if residency_ok and risks_ok:
        rows.append([InlineKeyboardButton(text=t(language, "btn_accept_all"), callback_data="disc:accept")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def serbia_status_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(language, "btn_status_boravak_temp"), callback_data="status:boravak_temporary")],
            [InlineKeyboardButton(text=t(language, "btn_status_boravak_perm"), callback_data="status:boravak_permanent")],
            [InlineKeyboardButton(text=t(language, "btn_status_serbia_visa"), callback_data="status:serbia_c_visa")],
            [InlineKeyboardButton(text=t(language, "btn_status_other"), callback_data="status:other")],
        ]
    )


def weekdays_keyboard(language: str, mask: int) -> InlineKeyboardMarkup:
    names = WEEKDAY_KEYS_RU if language == "ru" else WEEKDAY_KEYS_EN
    row: list[InlineKeyboardButton] = []
    for i, name in enumerate(names):
        marker = "✓ " if mask & (1 << i) else ""
        row.append(InlineKeyboardButton(text=f"{marker}{name}", callback_data=f"wd:{i}"))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            row,
            [InlineKeyboardButton(text=t(language, "btn_weekdays_done"), callback_data="wd:done")],
        ]
    )


def confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(language, "btn_save"), callback_data="reg:save"),
                InlineKeyboardButton(text=t(language, "btn_cancel"), callback_data="reg:cancel"),
            ]
        ]
    )
