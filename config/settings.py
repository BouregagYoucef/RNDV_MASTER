import os

# المسار الأساسي للمشروع (يفترض أن الملف يُنفذ من الجذر أو سيتم تعديله لاحقاً)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ----------------------------------------------------------------------
# إعدادات قاعدة البيانات (Database Settings)
# ----------------------------------------------------------------------
DB_NAME = 'appointment_manager.db'
DB_PATH = os.path.join(os.getcwd(), DB_NAME)

# ----------------------------------------------------------------------
# إعدادات الترخيص (Licensing Settings)
# ----------------------------------------------------------------------
LICENSE_FILE_NAME = 'license.json'
LICENSE_FILE_PATH = os.path.join(os.getcwd(), LICENSE_FILE_NAME)

# مسار المفتاح العام للتحقق من التوقيع
PUBLIC_KEY_PATH = os.path.join(os.getcwd(), 'config', 'public_key.pem')

# ----------------------------------------------------------------------
# إعدادات التطبيق العامة (General App Settings)
# ----------------------------------------------------------------------
APP_TITLE = "Appointment Management System"
DEFAULT_LANGUAGE = 'ar' # اللغة الافتراضية عند أول تشغيل

# ----------------------------------------------------------------------
# إعدادات حالة المواعيد (Appointment Status Constants)
# ----------------------------------------------------------------------
STATUS_CONFIRMED = 'Confirmed'
STATUS_ATTENDED = 'Attended'
STATUS_ABSENT = 'Absent'
STATUS_CANCELLED = 'Cancelled'

ALL_STATUSES = [
    STATUS_CONFIRMED,
    STATUS_ATTENDED,
    STATUS_ABSENT,
    STATUS_CANCELLED,
]
