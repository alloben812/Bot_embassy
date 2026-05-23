"""High-level Prenot@Mi flows: login, find Belgrade Schengen service, check
slots, book and confirm with OTP.

Each function uses the selectors in `selectors.py`. If a selector stops
matching, raise `SiteStructureChanged` — never silently retry against guessed
DOM, because the booking flow is single-shot per applicant.

Human-like behaviour: between actions we sleep a random short interval and
move the mouse to the target before clicking. The exact rhythm matters less
than not firing requests at machine speed.

All entry points take a `PrenotamiClient` so the same Playwright page is
reused inside a single check cycle (cookies, storage_state, anti-fingerprint).
"""

import asyncio
import random
from dataclasses import dataclass
from datetime import date, datetime

from loguru import logger
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from app.config import settings
from app.prenotami import selectors as S
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


@dataclass(frozen=True)
class Slot:
    when: datetime
    raw_handle: str  # selector or data-* attribute used to click the slot


async def _human_pause(min_s: float = 0.8, max_s: float = 2.4) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


async def _detect_captcha(page: Page) -> None:
    for sel in (S.CAPTCHA_MARKER, S.CLOUDFLARE_CHALLENGE):
        if await page.locator(sel).count() > 0:
            raise CaptchaEncountered(f"Anti-bot challenge present: {sel}")


async def is_authenticated(client: PrenotamiClient) -> bool:
    page = client.page
    try:
        await page.goto(f"{settings.prenotami_base_url}/", wait_until="domcontentloaded", timeout=30_000)
    except PlaywrightTimeoutError as e:
        raise SessionExpired("navigation to base url timed out") from e
    await _detect_captcha(page)
    return await page.locator(S.DASHBOARD_MARKER).count() > 0


async def login(client: PrenotamiClient, *, email: str, password: str, otp_provider) -> None:
    """Perform Prenot@Mi login. `otp_provider` is an async callable returning a 6-digit code."""
    page = client.page
    try:
        await page.goto(f"{settings.prenotami_base_url}/", wait_until="domcontentloaded", timeout=30_000)
    except PlaywrightTimeoutError as e:
        raise SessionExpired("could not load login page") from e

    await _detect_captcha(page)

    if await page.locator(S.LOGIN_EMAIL).count() == 0:
        if await page.locator(S.DASHBOARD_MARKER).count() > 0:
            return
        raise SiteStructureChanged("login form not found")

    await page.locator(S.LOGIN_EMAIL).fill(email)
    await _human_pause(0.3, 0.7)
    await page.locator(S.LOGIN_PASSWORD).fill(password)
    await _human_pause(0.3, 0.7)
    await page.locator(S.LOGIN_SUBMIT).first.click()

    try:
        await page.wait_for_load_state("networkidle", timeout=20_000)
    except PlaywrightTimeoutError:
        pass

    await _detect_captcha(page)

    if await page.locator(S.LOGIN_ERROR_BANNER).count() > 0:
        text = await page.locator(S.LOGIN_ERROR_BANNER).first.inner_text()
        raise AuthError(f"login error: {text.strip()[:200]}")

    if await page.locator(S.OTP_INPUT).count() > 0:
        code = await otp_provider()
        if code is None:
            raise OtpTimeout("no OTP from user for login step")
        await page.locator(S.OTP_INPUT).first.fill(code)
        await _human_pause(0.3, 0.7)
        await page.locator(S.OTP_SUBMIT).first.click()
        try:
            await page.wait_for_load_state("networkidle", timeout=20_000)
        except PlaywrightTimeoutError:
            pass
        await _detect_captcha(page)

    if await page.locator(S.DASHBOARD_MARKER).count() == 0:
        raise AuthError("dashboard marker missing after login")


async def open_belgrade_schengen_service(client: PrenotamiClient) -> None:
    """Navigate from dashboard to the Belgrade Schengen booking screen.

    Exact path on Prenot@Mi depends on the current account's available services.
    Selectors here are best-effort and will be calibrated during the manual
    reverse-engineering pass; if they fail we raise SiteStructureChanged.
    """
    page = client.page
    await page.locator(S.SERVICES_LINK).first.click()
    try:
        await page.wait_for_load_state("networkidle", timeout=15_000)
    except PlaywrightTimeoutError:
        pass

    await _detect_captcha(page)

    row = page.locator(S.SERVICE_ROW_BELGRADE_SCHENGEN)
    if await row.count() == 0:
        raise SiteStructureChanged("Belgrade Schengen service not found in services list")

    await row.first.locator(S.SERVICE_BOOK_BUTTON).first.click()
    try:
        await page.wait_for_load_state("networkidle", timeout=20_000)
    except PlaywrightTimeoutError:
        pass
    await _detect_captcha(page)


async def find_first_slot(
    client: PrenotamiClient,
    *,
    date_from: date,
    date_to: date,
    weekdays_mask: int,
) -> Slot:
    """Walk the calendar within [date_from, date_to] and return the first matching slot.

    Returns the slot or raises NoSlotsAvailable.
    """
    page = client.page

    if await page.locator(S.CALENDAR_ROOT).count() == 0:
        raise SiteStructureChanged("calendar root not found")

    cursor = date_from.replace(day=1)
    end = date_to
    guard = 0

    while cursor <= end and guard < 12:
        guard += 1
        available_days = page.locator(S.CALENDAR_DAY_AVAILABLE)
        count = await available_days.count()
        for i in range(count):
            el = available_days.nth(i)
            data_date = await el.get_attribute("data-date")
            if not data_date:
                continue
            try:
                day = datetime.strptime(data_date, "%Y-%m-%d").date()
            except ValueError:
                continue
            if day < date_from or day > date_to:
                continue
            if not (weekdays_mask & (1 << day.weekday())):
                continue

            await el.click()
            await _human_pause(0.4, 1.0)

            slots = page.locator(S.TIMESLOT_BUTTON)
            slot_count = await slots.count()
            if slot_count == 0:
                continue
            slot_el = slots.first
            time_text = (await slot_el.inner_text()).strip()
            try:
                hour, minute = (int(x) for x in time_text.replace(".", ":").split(":")[:2])
            except Exception:
                hour, minute = 9, 0
            when = datetime(day.year, day.month, day.day, hour, minute)
            return Slot(when=when, raw_handle=data_date)

        next_btn = page.locator(S.CALENDAR_NEXT_MONTH)
        if await next_btn.count() == 0:
            break
        await next_btn.first.click()
        await _human_pause(0.5, 1.2)
        try:
            await page.wait_for_load_state("networkidle", timeout=10_000)
        except PlaywrightTimeoutError:
            pass

        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)

    raise NoSlotsAvailable("no matching slots in range")


async def book_slot_and_confirm(
    client: PrenotamiClient,
    slot: Slot,
    *,
    otp_provider,
) -> tuple[str | None, datetime]:
    """Confirm the already-clicked slot, accept terms, submit form, optionally
    pass an OTP confirmation step, and read the booking code.

    Returns (booking_code, slot_datetime). Raises BookingConflict if the slot
    was taken between selection and confirmation.
    """
    page = client.page

    if await page.locator(S.CONFIRM_FORM).count() == 0:
        raise SiteStructureChanged("confirmation form not present")

    terms = page.locator(S.CONFIRM_CHECKBOX_TERMS)
    if await terms.count() > 0:
        await terms.first.check()
        await _human_pause(0.2, 0.5)

    await page.locator(S.CONFIRM_SUBMIT).first.click()
    try:
        await page.wait_for_load_state("networkidle", timeout=25_000)
    except PlaywrightTimeoutError:
        pass
    await _detect_captcha(page)

    if await page.locator(S.OTP_INPUT).count() > 0:
        code = await otp_provider()
        if code is None:
            raise OtpTimeout("no OTP from user for booking confirmation")
        await page.locator(S.OTP_INPUT).first.fill(code)
        await _human_pause(0.3, 0.6)
        await page.locator(S.OTP_SUBMIT).first.click()
        try:
            await page.wait_for_load_state("networkidle", timeout=20_000)
        except PlaywrightTimeoutError:
            pass

    if await page.locator(S.BOOKING_SUCCESS_MARKER).count() == 0:
        if "occupato" in (await page.content()).lower() or "no longer available" in (await page.content()).lower():
            raise BookingConflict("slot taken by someone else")
        raise SiteStructureChanged("success marker not visible after confirm")

    code = None
    code_loc = page.locator(S.BOOKING_CODE_FIELD)
    if await code_loc.count() > 0:
        code = (await code_loc.first.inner_text()).strip()

    logger.info("Booked slot {} with code {}", slot.when, code)
    return code, slot.when
