import hashlib
import flet as ft
import os
from typing import Optional, Dict, Any
from datetime import datetime

# استيراد المديرات والإعدادات
from config.settings import DB_PATH, APP_TITLE,LICENSE_FILE_PATH,PUBLIC_KEY_PATH
from db.database_manager import DatabaseManager
from utils.license_handler import LicenseManager
from utils.translation_manager import TranslationManager

# استيراد الواجهات (نفترض وجودها)
from views.login_view import LoginView
from views.license_view import LicenseView
#from views.dashboard_view import DashboardView # سنستخدمها كواجهة رئيسية


class AppState:
    """لتخزين حالة التطبيق والمديرات عالمياً."""
    def __init__(self, db, license_mgr, translation_mgr, theme_settings):
        self.db: DatabaseManager = db
        self.license: LicenseManager = license_mgr
        self.tr: TranslationManager = translation_mgr
        self.theme: Dict[str, str] = theme_settings
        self.logged_in_user: Optional[Dict] = None # معلومات موظف الاستقبال
        self.page: Optional[ft.Page] = None # حفظ مرجع لصفحة Flet الرئيسية




def setup_test_files():
    print("\n\nstf 0 -- Setting up test files...")
    """تهيئة ملفات ضرورية للاختبار."""
    if not os.path.exists('config'):
        os.makedirs('config')
        print("\n\nstf 0--the OS mkdir config file")
    # إنشاء ملف مفتاح عام وهمي (لا يُستخدم للتشفير الفعلي هنا)
    if not os.path.exists(PUBLIC_KEY_PATH):
        with open(PUBLIC_KEY_PATH, 'w') as f:
            f.write("---BEGIN PUBLIC KEY---TEST---END PUBLIC KEY---")
            print("\n\nstf 0--the OS create public key file")
    # إنشاء ملف ترخيص وهمي
    if not os.path.exists(LICENSE_FILE_PATH):
        with open(LICENSE_FILE_PATH, 'w') as f:
            f.write("{}")
            print("\n\nstf 0-- the OS create license file")


def run_database_tests():
    """تنفيذ سلسلة اختبارات للتحقق من عمل الدوال."""
    # تهيئة الملفات قبل الاختبار
    setup_test_files()
    print("\n\nrtf 0 -- Beginning database tests... and setup test files done.")
    # 1. الاتصال والتهيئة (يجب أن ينشئ الجداول تلقائياً)
    try:
        db_manager = DatabaseManager(db_path=DB_PATH)

        print("✅ rtf 1 -- the DB /conn has created , path is:", DB_PATH)
        pass_hashed = hashlib.sha256('password_123'.encode()).hexdigest()
        db_manager.add_user({
            'username': 'user',
            'password_hash': pass_hashed,
            'full_name': 'John Doe',
            'is_active': 1
        })
    except Exception as e:
        print("❌ rtf 1 -- failed to connect to DB",e)
        return


db_manager = DatabaseManager(db_path=DB_PATH)
def main(page: ft.Page):
    # 1. تهيئة قاعدة البيانات والمديرات
    #db_manager = DatabaseManager(db_path=DB_PATH)
    run_database_tests()
    #db_manager = DatabaseManager(db_path=DB_PATH)
    # تحميل إعدادات التنسيق واللغة
    theme_settings = db_manager.get_current_theme() or {} # استخدام قاموس فارغ كاحتياط
    settings = db_manager.get_settings()
    
    license_manager = LicenseManager(db_manager=db_manager)
    translation_manager = TranslationManager(db_manager=db_manager)
    
    # تحديث اللغة بناءً على الإعدادات المخزنة
    if settings and settings.get('language'):
        translation_manager.set_language(settings['language'])
        
    # تهيئة حالة التطبيق
    app_state = AppState(db_manager, license_manager, translation_manager, theme_settings)
    app_state.page = page # حفظ مرجع الصفحة

    # 2. دالة التوجيه الرئيسية بين المشاهد (Views)
    def _change_view(view_control: ft.Control):
        """تنظيف الصفحة وعرض واجهة مستخدم جديدة."""
        page.clean()
        page.add(view_control)
        page.update()

    # 3. دوال الانتقال الخاصة بنجاح العمليات
    def _on_auth_success(user_data: Optional[Dict]):
        """تُستدعى بعد التفعيل الناجح أو تسجيل الدخول الناجح."""
        if user_data:
            # نجاح تسجيل الدخول
            app_state.logged_in_user = user_data
            #_change_view(DashboardView(app_state))
            print(f"[{datetime.now().strftime('%H:%M:%S')}] User '{user_data.get('username')}' logged in successfully.")
            return False
        else:
            # نجاح التفعيل، يجب أن ننتقل لشاشة تسجيل الدخول
            _change_view(LoginView(app_state, _on_auth_success))


    # 4. تطبيق التنسيق العام (Flet Page Setup)
    page.title = APP_TITLE
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    if theme_settings:
        # Flet يستخدم الألوان بتنسيق #RRGGBB
        primary_color = theme_settings.get('Primary', ft.Colors.BLUE_700) 
        background_color = theme_settings.get('Background', ft.Colors.WHITE)
        surface_color = theme_settings.get('Surface_Cards', ft.Colors.WHITE)
        error_color = theme_settings.get('Error', ft.Colors.RED_500)

        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=primary_color,
                background=background_color,
                surface=surface_color,
                error=error_color,
            ),
        )

    # 5. بدء التشغيل: التحقق الأولي من الترخيص
    is_activated = license_manager.check_activation_status()
    
    if is_activated:
        # إذا كان مفعلاً: اعرض شاشة تسجيل الدخول
        _change_view(LoginView(app_state, _on_auth_success))
    else:
        # إذا لم يكن مفعلاً: اعرض شاشة التفعيل
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Application is NOT activated. Showing License View.")
        _change_view(LicenseView(app_state, _on_auth_success))

    page.update()

# تشغيل التطبيق
if __name__ == "__main__":
    # يجب تشغيل التطبيق في وضع سطح المكتب (Desktop Mode)
    ft.app(target=main)