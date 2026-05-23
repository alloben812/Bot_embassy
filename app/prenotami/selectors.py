"""All CSS/XPath selectors used to navigate Prenot@Mi.

These reflect the public Prenot@Mi site as of 2025–2026. The exact selectors
must be verified against a live session during the reverse-engineering step
(see plan, Verification §4). If selectors stop matching the page, raise
SiteStructureChanged from flows.py — never silently fall back.
"""

# --- Login page (https://prenotami.esteri.it/) ---
LOGIN_EMAIL = "input#Email"
LOGIN_PASSWORD = "input#Password"
LOGIN_SUBMIT = "button[type='submit'], input[type='submit']"
LOGIN_ERROR_BANNER = ".validation-summary-errors, .alert-danger"

# --- OTP step (in-page modal or dedicated page) ---
OTP_INPUT = "input[name='OTP'], input#OTP, input[type='text'][maxlength='6']"
OTP_SUBMIT = "button[type='submit']"

# --- Authenticated dashboard ---
DASHBOARD_MARKER = "a[href*='UserArea'], a[href*='/Services']"

# --- Service selection (Belgrade Schengen) ---
SERVICES_LINK = "a[href*='Services']"
SERVICE_ROW_BELGRADE_SCHENGEN = "tr:has-text('Visa - Visit / Tourism / Business')"
SERVICE_BOOK_BUTTON = "a:has-text('Prenota'), a:has-text('Book')"

# --- Calendar / slot picker ---
CALENDAR_ROOT = "#calendar, .calendar"
CALENDAR_DAY_AVAILABLE = ".day:not(.disabled):not(.unavailable):not(.empty)"
CALENDAR_NEXT_MONTH = "button.next, a.next"
CALENDAR_DAY_BY_DATE_TEMPLATE = "[data-date='{date}']"
TIMESLOT_LIST = ".time-slot, .slot"
TIMESLOT_BUTTON = "button.slot:not(.taken)"

# --- Booking confirmation ---
CONFIRM_FORM = "form[action*='Book'], form#bookingForm"
CONFIRM_CHECKBOX_TERMS = "input[type='checkbox'][name*='terms']"
CONFIRM_SUBMIT = "button[type='submit']:has-text('Conferma'), button:has-text('Confirm')"

# --- Booking success page ---
BOOKING_SUCCESS_MARKER = ".booking-success, :has-text('Prenotazione confermata')"
BOOKING_CODE_FIELD = ".booking-code, [data-booking-code]"
BOOKING_DATETIME_FIELD = ".booking-datetime, [data-booking-datetime]"

# --- Cloudflare / anti-bot markers ---
CLOUDFLARE_CHALLENGE = "#challenge-form, iframe[src*='challenges.cloudflare']"
CAPTCHA_MARKER = ".g-recaptcha, iframe[src*='recaptcha'], iframe[src*='hcaptcha']"
