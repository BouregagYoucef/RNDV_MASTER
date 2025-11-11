import os
from db.database_manager import DatabaseManager


# --- إعداد المسارات الأساسية ---
DB_NAME = 'appointment_manager.db'
DB_PATH= os.path.join(os.path.dirname(__file__), DB_NAME)
LICENSE_FILE_NAME = 'license.json'

LICENSE_FILE_PATH = 'license.json'
PUBLIC_KEY_PATH = 'config/public_key.pem' 
# --- إعدادات التطبيق العامة ---
APP_TITLE = "Appointment Management System"
DEFAULT_LANGUAGE = 'fr' 

# --- إعدادات حالة المواعيد ---
STATUS_CONFIRMED = 'Confirmed'
STATUS_ATTENDED = 'Attended'
STATUS_ABSENT = 'Absent'
STATUS_CANCELLED = 'Cancelled'
ALL_STATUSES = [STATUS_CONFIRMED, STATUS_ATTENDED, STATUS_ABSENT, STATUS_CANCELLED]


#--- إعدادات الثيمات ---
DEFAULT_THEME_ID = DatabaseManager.get_default_theme()
DEFAULT_THEME = DatabaseManager.get_current_theme() or {}

#------ الترجمة ------
ALL_TRANSLATION = DatabaseManager.get_translations()

SUPPORTED_LANGUAGES = {
    'Eng': 'English',
    'Ar': 'العربية',
    'Fr': 'Français',
}

ALL_SETTINGS = DatabaseManager.get_settings()