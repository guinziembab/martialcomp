# services/__init__.py

# Importer les services du dossier services
try:
    from .club_qr_service import ClubQRService
except ImportError:
    ClubQRService = None

try:
    from .event_reminder_service import EventReminderService
except ImportError:
    EventReminderService = None

# Importer LicenseNumberGenerator depuis le fichier services.py parent
try:
    from ..services import LicenseNumberGenerator
except ImportError:
    LicenseNumberGenerator = None

__all__ = [
    'ClubQRService',
    'EventReminderService',
    'LicenseNumberGenerator',
]
