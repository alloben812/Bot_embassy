# Bot Embassy

Telegram-бот для автоматического бронирования слотов на подачу шенгенской визы (тип C) в Посольстве Италии в Белграде через систему Prenot@Mi.

## Предупреждения

- **Резидентство**: Посольство Италии в Белграде принимает заявления только от резидентов Сербии (boravak) или держателей сербской визы C. Без такого статуса бронь не поможет — заявку отклонят на месте.
- **Запрет ботов**: МИД Италии официально заявляет, что записи, сделанные ботами или вредоносным ПО, будут аннулированы. Посольство Белграда дополнительно сообщает, что любое посредничество запрещено. Использование бота на ваш страх и риск.
- **OTP**: Prenot@Mi требует одноразовый код на email при логине и подтверждении брони. Бот не имеет доступа к вашей почте — он попросит вас прислать код в Telegram. Реагируйте быстро (по умолчанию 90 секунд).

## Стек

Python 3.12, aiogram 3, Playwright (Chromium + stealth), SQLAlchemy 2.0 (async), PostgreSQL 16, Redis 7, Docker Compose, Alembic.

## Быстрый старт (локально)

Подробная пошаговая инструкция: см. [QUICKSTART.md](./QUICKSTART.md).

Кратко:

```bash
cp .env.example .env
# Сгенерируйте ключ шифрования:
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Вставьте его в BOT_ENCRYPTION_KEY, добавьте BOT_TOKEN от @BotFather.

docker compose up -d postgres redis
docker compose run --rm bot alembic upgrade head
docker compose up bot worker
```

## Команды бота

- `/start` — приветствие и дисклеймер с двумя обязательными подтверждениями.
- `/register` — FSM-форма: креды Prenot@Mi, данные паспорта, статус в Сербии, диапазон дат, дни недели.
- `/start_monitor` — активировать мониторинг.
- `/pause`, `/stop`, `/status` — управление задачей.
- Любое 6-значное число — будет интерпретировано как OTP, если в данный момент бот его ждёт.

## Архитектура

```
bot (long polling) ──┐                ┌── Playwright (Chromium + stealth)
                     │                │
                     ├── Postgres ────┤
                     │   (encrypted)  │
                     │                │
worker (asyncio) ────┘                └── Prenot@Mi
        │
        └── OTP relay через Redis pub/sub ←→ bot ←→ пользователь
```

См. `/root/.claude/plans/kind-snacking-cupcake.md` для полного описания.

## Тесты

```bash
pip install -e ".[dev]"
pytest
```

## Замечание про селекторы Prenot@Mi

`app/prenotami/selectors.py` содержит селекторы для логина, календаря и формы подтверждения. До запуска в продакшн их нужно сверить с реальной страницей Prenot@Mi на живой сессии — см. `Verification` в плане. При расхождении бот не пытается «угадать» и поднимает `SiteStructureChanged`.
