import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.encryption import decrypt, encrypt
from app.db.models import Applicant
from app.db.repository import PrenotamiSessionRepository
from app.prenotami.stealth import new_stealth_context


class PrenotamiClient:
    """Manages a Playwright browser session for one applicant.

    Reuses cookies/storage_state from DB across check cycles. Persist new state
    after each successful interaction.
    """

    def __init__(self, applicant: Applicant, db: AsyncSession) -> None:
        self.applicant = applicant
        self.db = db
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> "PrenotamiClient":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.playwright_headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        storage_state = await self._load_storage_state()
        self._context = await new_stealth_context(
            self._browser,
            storage_state=storage_state,
            proxy_url=settings.playwright_proxy_url or None,
        )
        self._page = await self._context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            await self._persist_storage_state()
        except Exception as e:
            logger.warning("Failed to persist storage state: {}", e)
        if self._context is not None:
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

    @property
    def page(self) -> Page:
        assert self._page is not None, "Client not entered"
        return self._page

    @asynccontextmanager
    async def fresh_page(self):
        assert self._context is not None
        page = await self._context.new_page()
        try:
            yield page
        finally:
            await page.close()

    async def _load_storage_state(self) -> dict | None:
        record = await PrenotamiSessionRepository(self.db).get(self.applicant.id)
        if record is None:
            return None
        try:
            return json.loads(decrypt(record.state_json_encrypted))
        except Exception as e:
            logger.warning("Could not decrypt stored state, dropping: {}", e)
            await PrenotamiSessionRepository(self.db).invalidate(self.applicant.id)
            return None

    async def _persist_storage_state(self) -> None:
        if self._context is None:
            return
        state = await self._context.storage_state()
        encrypted = encrypt(json.dumps(state))
        await PrenotamiSessionRepository(self.db).upsert(
            applicant_id=self.applicant.id,
            state_json_encrypted=encrypted,
            expires_at=None,
        )

    async def invalidate_session(self) -> None:
        await PrenotamiSessionRepository(self.db).invalidate(self.applicant.id)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
