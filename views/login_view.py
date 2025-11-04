import flet as ft
import hashlib
from typing import Callable, Any
#from main import AppState # استيراد AppState الذي يحمل المديرات
from typing import Dict
import datetime

class LoginView(ft.Container):
    """
    واجهة تسجيل الدخول لموظفي الاستقبال.
    """
    
    def __init__(self, app_state, on_login_success: Callable[[Dict[str, Any]], None]):
        super().__init__()
        self.app = app_state
        self.tr = app_state.tr
        self.db = app_state.db
        self.on_login_success = on_login_success
        
        self.width = 400
        self.padding = 30
        self.theme = self.db.get_current_theme()
        self.translation = self.db.get_translations()
        self.theme_category =  None
        category = ("calendar","color","spacing","button","form","animation","typography","icon")
        print("\n\n======================================")
        print("---------- the theme data -----------")
        print("======================================")
        print("{")
        for key in self.theme:
            print(f"\"{key}\":", self.theme[key])
        print("}")
        print("\n\n======================================")
        print("------- the translation data -------")
        print("======================================")
        print("{")
        for i in self.translation:
            print(f"\"{i}\":", self.translation[i])
        print("}")

        print("\n\n======================================")
        print("------- the category theme -------")
        print("======================================")
        print("{")
        for i in category:
            print(f"==== {i} =====")
            print(f"\"{i}\":", self.db.get_theme_by_category(i))
        print("}")



        self.bgcolor = self.app.theme.get('Surface_Cards', ft.Colors.WHITE)
        self.border_radius = 10
        
        
        # حقول الإدخال
        self.username_field = ft.TextField(
            label=self.tr.get_text('username_label', "اسم المستخدم"),
            prefix_icon=ft.Icons.PERSON,
            text_align=ft.TextAlign.LEFT,
            width=300
        )
        self.password_field = ft.TextField(
            label=self.tr.get_text('password_label', "كلمة المرور"),
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            text_align=ft.TextAlign.LEFT,
            on_submit=self._attempt_login, # يمكن تسجيل الدخول بالضغط على Enter
            width=300
        )
        self.error_message = ft.Text("", color=self.app.theme.get('Error', ft.Colors.RED_500))
        self.content = self._build_ui()
    def _attempt_login(self, e: ft.ControlEvent):
        """
        محاولة تسجيل الدخول: التحقق من اسم المستخدم وكلمة المرور.
        """
        try:
            username = self.username_field.value
            password = self.password_field.value
        except Exception as ex:
            self.error_message.value = self.tr.get_text('login_error', "حدث خطأ أثناء محاولة تسجيل الدخول.")
            self.update()
            return
        if not username or not password:
            self.error_message.value = self.tr.get_text('empty_fields', "الرجاء إدخال اسم المستخدم وكلمة المرور.")
            self.update()
            return
        
        # 1. استرداد بيانات المستخدم من DB
        user_record = self.db.get_user_by_username(username)
        
        if user_record:
            # 2. تشفير كلمة المرور المُدخلة ومقارنتها بالهاش المخزن
            input_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if input_hash == user_record.get('password_hash'):
                # 3. نجاح تسجيل الدخول
                self.error_message.value = ""
                # تسجيل الحدث في Audit Logs
                self.db.execute_query(
                    "INSERT INTO Audit_Logs (timestamp, action_type, details, user_id) VALUES (?, ?, ?, ?)",
                    (datetime.datetime.now().isoformat(), 'LOGIN_SUCCESS', 'User logged in successfully', user_record.get('user_id')),
                    commit=True
                )
                self.on_login_success(dict(user_record)) # استدعاء الدالة في main.py
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] User '{username}' logged in successfully.")
                return
            else:
                # 4. فشل: كلمة المرور خاطئة
                self.error_message.value = self.tr.get_text('wrong_password', "كلمة المرور خاطئة.")
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Failed login attempt for user '{username}': Wrong password.")

        else:
            # 5. فشل: اسم المستخدم غير موجود
            self.error_message.value = self.tr.get_text('user_not_found', "اسم المستخدم غير موجود.")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Failed login attempt: User '{username}' not found.")
            
        # تحديث الواجهة لعرض رسالة الخطأ
        self.password_field.value = ""
        self.update()
        
    def _build_ui(self):
        """بناء تخطيط واجهة المستخدم Flet."""
        
        # إنشاء زر تسجيل الدخول
        login_button = ft.ElevatedButton(
            text=self.tr.get_text('login_button', "تسجيل الدخول"),
            on_click=self._attempt_login,
            color=self.app.theme.get('Primary'),
            width=300
        )
        
        return ft.Column(
            controls=[
                ft.Text(self.tr.get_text('app_title', "إدارة المواعيد"), size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20),
                self.username_field,
                self.password_field,
                self.error_message,
                login_button,
                ft.Container(height=10),
                ft.Text(f"{self.tr.get_text('version', 'Version')}: 1.0", size=10, color=ft.Colors.BLACK54)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        )

# ملاحظة: يجب أن تقوم بإنشاء ملفviews/license_view.py كبديل لواجهة التفعيل