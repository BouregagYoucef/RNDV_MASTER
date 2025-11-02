import os

# --- إعداد المسارات الأساسية ---
DB_NAME = 'appointment_manager.db'
DB_PATH = os.path.join(os.getcwd(), DB_NAME)
DB_PATH= os.path.join(os.path.dirname(__file__), DB_NAME)
LICENSE_FILE_NAME = 'license.json'
LICENSE_FILE_PATH = os.path.join(os.getcwd(), LICENSE_FILE_NAME)
PUBLIC_KEY_PATH = os.path.join(os.getcwd(), 'config', 'public_key.pem')
LICENSE_FILE_PATH = 'license.json'
PUBLIC_KEY_PATH = 'config/public_key.pem' 
# --- إعدادات التطبيق العامة ---
APP_TITLE = "Appointment Management System"
DEFAULT_LANGUAGE = 'ar' 

# --- إعدادات حالة المواعيد ---
STATUS_CONFIRMED = 'Confirmed'
STATUS_ATTENDED = 'Attended'
STATUS_ABSENT = 'Absent'
STATUS_CANCELLED = 'Cancelled'
ALL_STATUSES = [STATUS_CONFIRMED, STATUS_ATTENDED, STATUS_ABSENT, STATUS_CANCELLED]

# --- مفاتيح التنسيق الافتراضية (Theme Keys) ---
# تستخدم كدليل عند تهيئة جدول 'theme' لأول مرة
THEME_KEYS = [
    "Primary", "Primary_Light", "Primary_Dark",
    "Secondary", "Secondary_Light", "Secondary_Dark",
    "Neutral_Dark", "Neutral_Medium", "Neutral_Light",
    "Background", "Surface_Cards", "Error", "Warning", "Success",
    "Primary_font", "Headings_font"
]