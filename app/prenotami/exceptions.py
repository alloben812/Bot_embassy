class PrenotamiError(Exception):
    """Base for all Prenot@Mi flow errors."""


class AuthError(PrenotamiError):
    """Wrong email/password or login flow broken."""


class OtpTimeout(PrenotamiError):
    """User did not provide OTP in time."""


class NoSlotsAvailable(PrenotamiError):
    """Calendar shows no free slots in the desired range."""


class CaptchaEncountered(PrenotamiError):
    """Anti-bot CAPTCHA detected; cannot proceed automatically."""


class SiteStructureChanged(PrenotamiError):
    """DOM does not match expected selectors."""


class SessionExpired(PrenotamiError):
    """Saved cookies/state are no longer valid."""


class BookingConflict(PrenotamiError):
    """Slot was taken by someone else between detection and booking."""
