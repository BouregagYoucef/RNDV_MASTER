import flet as ft
from db.database_manager import DatabaseManager
from utils.license_handler import LicenseManager
from utils.translation_manager import TranslationManager
from config.settings import DB_PATH, APP_TITLE
from views.login_view import LoginView # استيراد الواجهة الجديدة

# -------------------------------------------------------------------
# ملاحظة: يجب أن تكون لديك شاشة "DashboardView" للانتقال إليها بعد الدخول
def navigate_to_dashboard(user_info):
    """دالة وهمية للتحويل إلى لوحة التحكم."""
    print(f"Login successful for user: {user_info.get('full_name')}. Redirecting...")
    # هنا يجب أن يتم تحديث محتوى الصفحة (page.controls) لعرض لوحة التحكم

# -------------------------------------------------------------------

def main(page: ft.Page):
    # 1. تهيئة قاعدة البيانات والمديرات
    db_manager = DatabaseManager(db_path=DB_PATH)
    license_manager = LicenseManager(db_manager=db_manager)
    translation_manager = TranslationManager(db_manager=db_manager)
    
    # تهيئة اللغة بناءً على الإعدادات المخزنة
    settings = db_manager.get_settings()
    if settings:
        translation_manager.set_language(settings.get('language', 'ar'))
        page.title = APP_TITLE
    
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT

    # 2. تعريف دالة للانتقال إلى الواجهة الرئيسية بعد الدخول
    def on_login_success(user_info):
        # مسح الواجهة الحالية وإضافة واجهة لوحة التحكم
        page.clean()
        page.add(ft.Text(f"مرحباً يا {user_info.get('full_name')}! جاري تحميل النظام الرئيسي..."))
        # يمكنك هنا إضافة المنطق لتحميل DashboardView
        page.update()

    # 3. عرض واجهة تسجيل الدخول
    login_view = LoginView(db_manager, license_manager, translation_manager, on_login_success)
    
    # 4. إذا لم يكن هناك أي مستخدم، قم بإنشاء مستخدم افتراضي للتجربة (ضروري لأول مرة)
    if not db_manager.get_user_by_username('admin'):
        db_manager.add_user({
            'username': 'admin',
            'password_hash': 'admin123', # يجب تشفيرها لاحقاً
            'full_name': 'Admin User'
        })
        
    page.add(login_view)
    page.update()


if __name__ == "__main__":
    # تشغيل التطبيق
    ft.app(target=main)