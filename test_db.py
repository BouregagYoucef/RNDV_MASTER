import os
from datetime import datetime
from db.database_manager import DatabaseManager
from utils.license_handler import LicenseManager # سنستدعي مدير الترخيص للتأكد من التكامل
from config.settings import DEFAULT_LANGUAGE
import hashlib # للاختبارات

DB_NAME = 'appointment_manager.db'
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)


# يجب التأكد من وجود ملفات الترجمة والمفتاح العام الوهمية للتجربة
# قم بإنشاء ملف license.json فارغ وملف config/public_key.pem وهمي
LICENSE_FILE_PATH = 'license.json'
PUBLIC_KEY_PATH = 'config/public_key.pem' 

def setup_test_files():
    """تهيئة ملفات ضرورية للاختبار."""
    if not os.path.exists('config'):
        os.makedirs('config')
        print("0--the OS mkdir config file")
    # إنشاء ملف مفتاح عام وهمي (لا يُستخدم للتشفير الفعلي هنا)
    if not os.path.exists(PUBLIC_KEY_PATH):
        with open(PUBLIC_KEY_PATH, 'w') as f:
            f.write("---BEGIN PUBLIC KEY---TEST---END PUBLIC KEY---")
            print("0--the OS create public key file")
    # إنشاء ملف ترخيص وهمي
    if not os.path.exists(LICENSE_FILE_PATH):
        with open(LICENSE_FILE_PATH, 'w') as f:
            f.write("{}")
            print("0-- the OS create license file")


def run_database_tests():
    """تنفيذ سلسلة اختبارات للتحقق من عمل الدوال."""

    print("0  -- Beginning database tests...")
    
    # تهيئة الملفات قبل الاختبار
    setup_test_files()
    
    # 1. الاتصال والتهيئة (يجب أن ينشئ الجداول تلقائياً)
    try:
        db_manager = DatabaseManager(db_path=DB_PATH)
  
        print("✅ 1 -- the DB /conn has created , path is:", DB_PATH)   
    except Exception as e:
        print("❌ 1 -- failed to connect to DB",e)
        return

    # 2. اختبار الإعدادات الافتراضية والتنسيق (Theme)
    try:
        db_manager.set_default_settings()
        db_manager.set_default_theme()
        settings = db_manager.get_settings()
        theme = db_manager.get_theme_settings()
    except Exception as e:
        print("❌ 2 -- failed to retrieve settings/theme:", e)
        return

    if settings and theme:
        print("✅ 2 --default settings of company has imported successfully",settings.get('company_name'))
        print("✅ 2 --default theme has imported successfully",theme.get('Primary'))
    else:
        print("❌ 2 --failed import theme/settings because they are None")
        return
    
    # 3. اختبار إضافة/استرداد مستخدم (لتسجيل الدخول)
    test_password_hash = hashlib.sha256("12345".encode()).hexdigest()
    user_data = {'username': 'test_reception', 'password_hash': test_password_hash, 'full_name': 'استقبال تجريبي'}
    user_id = db_manager.add_user(user_data)
    
    if user_id:
        print("✅ 3 -- the user has added successfully:", user_id)
        user = db_manager.get_user_by_username('test_reception')
        if user and user.get('password_hash') == test_password_hash:
            print("✅ 3 -- the user has retrieved successfully for login.")
        else:
            print("❌ 3 -- failed to retrieve user after addition.")
    else:
        print("❌ 3 -- failed to add user.")

    # 4. اختبار مدير الترخيص (تكامل LicenseManager)

    #اختبار اضافة ترخيص في  licenses table
    try:
        license_data = {
            'machine_id': 'TEST_MACHINE_ID_12345',
            'license_key': 'TEST_LICENSE_KEY_ABCDE',
            'is_active': 1,
            'activation_date': datetime.now().isoformat(),
            'expiry_date': (datetime.now().replace(year=datetime.now().year + 1)).isoformat()
        }
        db_manager.set_license_info(license_data)
        print("✅ 4 -- license info has added to DB for testing.")
    except Exception as e:
        print(f"❌ 4 -- failed to add license info to DB: {e}")

    print("\n--- 🔑 testing LicenseManager ---")
    try:
        license_manager = LicenseManager(db_manager)
        current_id = license_manager.get_current_machine_id()
        license_info = db_manager.get_license_info()
        print("🔑 License Info from DB:", license_info)
        print("🔑 Current Machine ID:", current_id)
        if license_info and current_id:
            print(f"✅ 4 -- machine id has generated: {current_id[:10]}...")
            print(f"✅ 4 -- status: {'active' if license_info.get('is_active') == 1 else 'inactive'}")
        else:
            print("❌ 4 -- failed to generate or store license/machine information.")

    except Exception as e:
        print(f"❌ 4 -- failed to initialize/run LicenseManager: {e}")
    
    # 5. اختبار إضافة عميل (لتجربة الدوال الأخرى لاحقاً)
    client_data = {'full_name': 'أحمد سعيد', 'phone_number': '0666112233', 'email': 'ahmed@example.com'}
    client_id = db_manager.add_client(client_data)
    
    if client_id:
        print(f"✅ 5 -- the client has added successfully. ID = {client_id}")
    else:
        print("❌ 5 -- failed to add client.")

    print("\n--- ✅ database tests completed successfully ---")


if __name__ == "__main__":
    # تنظيف قاعدة البيانات القديمة (اختياري، للتأكد من اختبار الإنشاء)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Test :🗑️ the old database has been removed: {DB_PATH}")
        
    run_database_tests()