TEXTS: dict[str, dict[str, str]] = {
    "ru": {
        "welcome": (
            "Здравствуйте! Это бот для записи на подачу шенгенской визы (тип C) "
            "в Посольство Италии в Белграде через систему Prenot@Mi.\n\n"
            "Бот будет периодически проверять свободные слоты и при появлении подходящей даты "
            "автоматически забронирует её, попросив у вас OTP-код, который Prenot@Mi высылает на email."
        ),
        "disclaimer_title": "Прежде чем продолжить — два важных предупреждения",
        "disclaimer_body": (
            "1) Резидентство.\n"
            "Посольство Италии в Белграде принимает заявления только от резидентов Сербии "
            "(boravak — временный или постоянный ВНЖ) или держателей сербской визы C. "
            "Если у вас нет одного из этих статусов, ваша заявка будет отклонена даже при успешной брони — "
            "бот не сможет это изменить.\n\n"
            "2) Запрет ботов на стороне посольства.\n"
            "МИД Италии официально заявляет: «Записи, сделанные ботами или вредоносным ПО, будут аннулированы». "
            "Посольство Белграда дополнительно сообщает: «Любое посредничество запрещено». "
            "Используя этот бот, вы принимаете риск аннулирования брони и возможные последствия со стороны посольства.\n\n"
            "Подтвердите оба пункта, чтобы продолжить."
        ),
        "btn_confirm_residency": "Подтверждаю резидентство в Сербии",
        "btn_confirm_residency_done": "Подтверждено: резидентство",
        "btn_confirm_risks": "Принимаю риски использования бота",
        "btn_confirm_risks_done": "Подтверждено: риски",
        "btn_accept_all": "Согласиться и начать регистрацию",
        "disclaimer_accepted": "Согласие записано. Начнём регистрацию: /register",
        "disclaimer_required": "Сначала подтвердите оба пункта дисклеймера.",
        "help": (
            "Команды:\n"
            "/start — приветствие и дисклеймер\n"
            "/register — заполнить данные для бронирования\n"
            "/start_monitor — запустить мониторинг слотов\n"
            "/pause — приостановить мониторинг\n"
            "/stop — остановить и удалить задачу\n"
            "/status — текущий статус задачи\n"
            "/help — эта справка"
        ),
        "register_already": "Данные уже сохранены. Используйте /stop, чтобы удалить и начать заново.",
        "register_need_disclaimer": "Сначала примите дисклеймер: /start",
        "register_start": "Введите email от Prenot@Mi (он же логин).",
        "register_password": "Введите пароль от Prenot@Mi. После сохранения сообщение будет удалено.",
        "register_full_name": "Введите ФИО как в загранпаспорте (латиницей).",
        "register_passport": "Введите номер загранпаспорта (буквы и цифры без пробелов).",
        "register_birth": "Введите дату рождения в формате ДД.ММ.ГГГГ.",
        "register_citizenship": "Гражданство (двухбуквенный код, например RU).",
        "register_serbia_status": "Ваш статус в Сербии:",
        "btn_status_boravak_temp": "Boravak (временный)",
        "btn_status_boravak_perm": "Boravak (постоянный)",
        "btn_status_serbia_visa": "Сербская виза C",
        "btn_status_other": "Другое",
        "register_serbia_id": "Введите номер документа резидентства (boravak/виза).",
        "register_date_from": "С какой даты искать слоты? Формат ДД.ММ.ГГГГ.",
        "register_date_to": "По какую дату искать? Формат ДД.ММ.ГГГГ.",
        "register_weekdays": "Выберите дни недели (можно несколько), потом нажмите «Готово».",
        "btn_weekdays_done": "Готово",
        "register_summary": "Проверьте данные перед сохранением:\n{summary}",
        "btn_save": "Сохранить",
        "btn_cancel": "Отмена",
        "register_saved": "Данные сохранены. Запустить мониторинг: /start_monitor",
        "register_cancelled": "Регистрация отменена.",
        "register_invalid_date": "Неверный формат даты. Попробуйте ещё раз: ДД.ММ.ГГГГ.",
        "register_invalid_email": "Это не похоже на email. Попробуйте ещё раз.",
        "register_date_range_invalid": "Дата «до» должна быть позже даты «с» и не дальше 6 месяцев вперёд.",
        "monitor_no_data": "Нет сохранённых данных. Сначала /register.",
        "monitor_started": "Мониторинг запущен. Я уведомлю, когда слот будет найден.",
        "monitor_paused": "Мониторинг приостановлен. Возобновить: /start_monitor.",
        "monitor_stopped": "Задача мониторинга удалена.",
        "monitor_already_running": "Мониторинг уже запущен.",
        "status_template": (
            "Задача #{task_id}\n"
            "Статус: {status}\n"
            "Диапазон дат: {date_from} — {date_to}\n"
            "Последняя проверка: {last_check}\n"
            "Следующая проверка: {next_check}\n"
            "Всего проверок: {attempts}"
        ),
        "otp_request": (
            "Prenot@Mi запрашивает одноразовый код.\n"
            "Откройте email, найдите письмо от Prenot@Mi и пришлите сюда 6-значный код в течение {timeout} секунд."
        ),
        "otp_timeout": "Время ожидания OTP истекло. Попробую снова в следующий цикл.",
        "otp_received": "Код получен, продолжаю.",
        "otp_invalid": "Не похоже на 6-значный код. Пришлите только цифры.",
        "otp_no_request": "Сейчас никакого OTP не ожидается.",
        "booking_success": (
            "✔ Бронь подтверждена.\n"
            "Дата и время: {slot}\n"
            "Код в Prenot@Mi: {code}\n\n"
            "Обязательно войдите на prenotami.esteri.it, чтобы убедиться, что бронь видна и распечатать подтверждение."
        ),
        "booking_failed": "Не удалось завершить бронирование: {reason}. Продолжаю мониторинг.",
        "auth_error": "Не удалось войти в Prenot@Mi. Проверьте логин/пароль и зарегистрируйтесь заново через /stop и /register.",
        "captcha_alert": "Сайт показал CAPTCHA. Мониторинг временно остановлен. Возобновить: /start_monitor.",
    },
    "en": {
        "welcome": (
            "Hello! This bot books Schengen (type C) visa appointments at the Italian Embassy in Belgrade "
            "via Prenot@Mi. It checks slots periodically and books the first matching one, asking you for "
            "the OTP code that Prenot@Mi sends to your email."
        ),
        "disclaimer_title": "Two important warnings before you continue",
        "disclaimer_body": (
            "1) Residency.\n"
            "The Italian Embassy in Belgrade only accepts applications from residents of Serbia (boravak) or "
            "holders of a Serbian C-visa. If you do not hold one of these statuses, your application will be "
            "rejected even after a successful booking — the bot cannot change this.\n\n"
            "2) Bots are forbidden by the embassy.\n"
            "Italian MFA: 'Appointments booked by means of bots or malicious software will be eliminated.' "
            "Embassy of Belgrade: 'Any intermediation is prohibited.' By using this bot you accept the risk "
            "that the booking may be cancelled."
        ),
        "btn_confirm_residency": "I confirm Serbian residency",
        "btn_confirm_residency_done": "Confirmed: residency",
        "btn_confirm_risks": "I accept the risks",
        "btn_confirm_risks_done": "Confirmed: risks",
        "btn_accept_all": "Agree and start registration",
        "disclaimer_accepted": "Recorded. Start registration: /register",
        "disclaimer_required": "Please confirm both points first.",
        "help": (
            "Commands:\n"
            "/start — welcome and disclaimer\n"
            "/register — fill booking data\n"
            "/start_monitor — start slot monitoring\n"
            "/pause — pause monitoring\n"
            "/stop — stop and delete the task\n"
            "/status — current task status\n"
            "/help — this help"
        ),
        "register_already": "Already registered. Use /stop to delete and start over.",
        "register_need_disclaimer": "Accept the disclaimer first: /start",
        "register_start": "Enter your Prenot@Mi email (login).",
        "register_password": "Enter your Prenot@Mi password. Your message will be deleted after saving.",
        "register_full_name": "Enter full name as in passport (Latin letters).",
        "register_passport": "Enter passport number (letters and digits, no spaces).",
        "register_birth": "Enter date of birth as DD.MM.YYYY.",
        "register_citizenship": "Citizenship (2-letter code, e.g. RU).",
        "register_serbia_status": "Your status in Serbia:",
        "btn_status_boravak_temp": "Boravak (temporary)",
        "btn_status_boravak_perm": "Boravak (permanent)",
        "btn_status_serbia_visa": "Serbian C-visa",
        "btn_status_other": "Other",
        "register_serbia_id": "Enter the residency document number (boravak/visa).",
        "register_date_from": "Search slots from which date? DD.MM.YYYY.",
        "register_date_to": "Until which date? DD.MM.YYYY.",
        "register_weekdays": "Pick weekdays (multi-select), then tap Done.",
        "btn_weekdays_done": "Done",
        "register_summary": "Review before saving:\n{summary}",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
        "register_saved": "Saved. Start monitoring: /start_monitor",
        "register_cancelled": "Registration cancelled.",
        "register_invalid_date": "Invalid date. Please enter DD.MM.YYYY.",
        "register_invalid_email": "Not an email. Try again.",
        "register_date_range_invalid": "End date must be after start date and within 6 months.",
        "monitor_no_data": "No data saved. Run /register first.",
        "monitor_started": "Monitoring started. I'll notify you when a slot is found.",
        "monitor_paused": "Monitoring paused. Resume: /start_monitor.",
        "monitor_stopped": "Monitoring task deleted.",
        "monitor_already_running": "Monitoring is already running.",
        "status_template": (
            "Task #{task_id}\n"
            "Status: {status}\n"
            "Date range: {date_from} — {date_to}\n"
            "Last check: {last_check}\n"
            "Next check: {next_check}\n"
            "Total checks: {attempts}"
        ),
        "otp_request": (
            "Prenot@Mi asks for a one-time code.\n"
            "Open your email, find the message from Prenot@Mi and send the 6-digit code here within {timeout} seconds."
        ),
        "otp_timeout": "OTP wait timed out. Will retry next cycle.",
        "otp_received": "Code received, continuing.",
        "otp_invalid": "That doesn't look like a 6-digit code. Digits only please.",
        "otp_no_request": "No OTP is being requested right now.",
        "booking_success": (
            "Booking confirmed.\n"
            "Date and time: {slot}\n"
            "Prenot@Mi code: {code}\n\n"
            "Please log in to prenotami.esteri.it to verify the booking and print the confirmation."
        ),
        "booking_failed": "Could not finalize booking: {reason}. Continuing monitoring.",
        "auth_error": "Login to Prenot@Mi failed. Check credentials and re-register via /stop and /register.",
        "captcha_alert": "Site showed a CAPTCHA. Monitoring paused. Resume: /start_monitor.",
    },
}


def t(language: str, key: str, **kwargs: object) -> str:
    lang = language if language in TEXTS else "ru"
    template = TEXTS[lang].get(key) or TEXTS["ru"].get(key) or key
    if kwargs:
        return template.format(**kwargs)
    return template
