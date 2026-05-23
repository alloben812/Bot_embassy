import random

from playwright.async_api import Browser, BrowserContext

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


async def new_stealth_context(
    browser: Browser,
    *,
    storage_state: dict | None = None,
    proxy_url: str | None = None,
) -> BrowserContext:
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1366 + random.randint(-20, 20), "height": 768 + random.randint(-20, 20)},
        locale="ru-RU",
        timezone_id="Europe/Belgrade",
        extra_http_headers={"Accept-Language": "ru-RU,sr;q=0.9,en;q=0.8"},
        storage_state=storage_state,
        proxy={"server": proxy_url} if proxy_url else None,
    )

    try:
        from playwright_stealth import stealth_async  # type: ignore[import-not-found]

        async def apply(page):
            await stealth_async(page)

        context.on("page", lambda p: p.evaluate("() => true") and apply(p))
    except Exception:
        pass

    await context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'sr', 'en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = { runtime: {} };
        """
    )

    return context
