import flet as ft
from typing import Callable
from db.database_manager import DatabaseManager
from utils.license_handler import LicenseManager
from utils.translation_manager import TranslationManager

# تحديد بعض الألوان والثوابت
PRIMARY_COLOR = ft.Colors.BLUE_700
ERROR_COLOR = ft.Colors.RED_500
CARD_COLOR = ft.Colors.WHITE

class LoginView(ft.Control):
    """
    واجهة تسجيل الدخول. تتحقق من الترخيص أولاً ثم بيانات المستخدم.
    """
    def __init__(self, 
                 db_manager: DatabaseManager, 
                 license_manager: LicenseManager, 
                 translation_manager: TranslationManager,
                 on_login_success: Callable):
        
        super().__init__()
        self.db = db_manager
        self.license = license_manager
        self.trans = translation_manager
        self.on_login_success = on_login_success
        
        # حقول النموذج (Form Fields)
        self.username_field = ft.TextField(
            label=self.trans.get_text('username_label', 'Username'),
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            width=300
        )
        self.password_field = ft.TextField(
            label=self.trans.get_text('password_label', 'Password'),
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            width=300
        )
        self.error_message = ft.Text("", color=ERROR_COLOR)
        
        # زر تسجيل الدخول - يجب تعريفه قبل _check_initial_status
        self.login_button = ft.ElevatedButton(
            text=self.trans.get_text('login_btn', 'Login'),
            icon=ft.Icons.LOGIN,
            on_click=self._handle_login,
            width=300
        )
        
        # حقول الترخيص
        self.license_status_text = ft.Text("", weight=ft.FontWeight.BOLD)
        self.license_button = ft.ElevatedButton(
            text=self.trans.get_text('activate_btn', 'Activate License'),
            icon=ft.Icons.VPN_KEY,
            on_click=self._show_license_dialog,
            width=300
        )
        
        # تهيئة واجهة المستخدم عند الإنشاء
        self._check_initial_status()

    # ---------------------------------
    # منطق التحقق من الترخيص
    # ---------------------------------
    
    def _check_initial_status(self):
        """التحقق من حالة الترخيص وتحديث الواجهة."""
        try:
            if self.license.check_activation_status():
                self.license_status_text.value = self.trans.get_text('license_active', 'License: Active')
                self.license_status_text.color = ft.Colors.GREEN_700
                self.license_button.visible = False
                self.login_button.disabled = False
            else:
                self.license_status_text.value = self.trans.get_text('license_inactive', 'License: Inactive')
                self.license_status_text.color = ERROR_COLOR
                self.license_button.visible = True
                self.login_button.disabled = True
            
            print("✅ تم تحديث حالة الترخيص في الواجهة")
            
        except Exception as e:
            print(f"❌ خطأ في التحقق من حالة الترخيص: {e}")
            # حالة افتراضية في حالة الخطأ
            self.license_status_text.value = "License: Check Failed"
            self.license_status_text.color = ft.Colors.ORANGE_700
            self.license_button.visible = True
            self.login_button.disabled = True

    def _show_license_dialog(self, e):
        """عرض نافذة منبثقة لإدخال/تفعيل الترخيص."""
        try:
            # 1. عرض Machine ID للمستخدم ليرسله
            machine_id = self.license.get_current_machine_id()
            
            # 2. إنشاء حقل لرفع ملف الترخيص (license.json)
            file_picker = ft.FilePicker(on_result=self._pick_license_file)
            self.page.overlay.append(file_picker)
            
            # 3. إنشاء النافذة المنبثقة
            self.license_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(self.trans.get_text('license_activation', 'License Activation')),
                content=ft.Column([
                    ft.Text(self.trans.get_text('send_id_note', 'Please send this Machine ID to the distributor:')),
                    ft.Container(
                        content=ft.SelectableText(
                            machine_id, 
                            style=ft.TextThemeStyle.BODY_MEDIUM,
                            selectable=True
                        ),
                        bgcolor=ft.Colors.GREY_100,
                        padding=10,
                        border_radius=8,
                        width=400
                    ),
                    ft.Divider(),
                    ft.Text(self.trans.get_text('upload_license', 'Upload the received license.json file:')),
                    ft.ElevatedButton(
                        text=self.trans.get_text('upload_file_btn', 'Select License File'),
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=lambda _: file_picker.pick_files(
                            allowed_extensions=["json"],
                            allow_multiple=False
                        )
                    ),
                ], tight=True, height=280),
                actions=[
                    ft.TextButton(
                        self.trans.get_text('close_btn', 'Close'), 
                        on_click=lambda e: self._close_dialog()
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.dialog = self.license_dialog
            self.license_dialog.open = True
            self.page.update()
            
        except Exception as e:
            print(f"❌ خطأ في عرض نافذة الترخيص: {e}")
            self.error_message.value = f"Error opening license dialog: {e}"
            self.error_message.update()

    def _pick_license_file(self, e: ft.FilePickerResultEvent):
        """معالجة اختيار ملف الترخيص ومحاولة التفعيل."""
        try:
            if e.files and e.files[0].path:
                file_path = e.files[0].path
                print(f"📁 تم اختيار ملف: {file_path}")
                
                # محاولة التفعيل
                if self.license.activate_from_file(file_path):
                    self.error_message.value = self.trans.get_text('activation_success', 'Activation successful! You can now log in.')
                    self.error_message.color = ft.Colors.GREEN_700
                    self._check_initial_status() # تحديث الواجهة بعد التفعيل
                    self._close_dialog()
                else:
                    self.error_message.value = self.trans.get_text('activation_failed', 'Activation failed. Invalid license file or Machine ID mismatch.')
                    self.error_message.color = ERROR_COLOR
                
                self.error_message.update()
            else:
                print("❌ لم يتم اختيار أي ملف")
                
        except Exception as e:
            print(f"❌ خطأ في معالجة ملف الترخيص: {e}")
            self.error_message.value = f"Error processing license file: {e}"
            self.error_message.color = ERROR_COLOR
            self.error_message.update()

    def _close_dialog(self):
        """إغلاق النافذة المنبثقة."""
        try:
            if hasattr(self, 'license_dialog') and self.license_dialog:
                self.license_dialog.open = False
                self.page.update()
        except Exception as e:
            print(f"❌ خطأ في إغلاق النافذة: {e}")

    # ---------------------------------
    # منطق تسجيل الدخول
    # ---------------------------------
    
    def _handle_login(self, e):
        """التحقق من بيانات المستخدم."""
        try:
            username = self.username_field.value.strip()
            password = self.password_field.value
            
            if not username or not password:
                self.error_message.value = self.trans.get_text('fill_all_fields', 'Please fill all fields.')
                self.error_message.color = ERROR_COLOR
                self.error_message.update()
                return
            
            user = self.db.get_user_by_username(username)
            
            if not user:
                self.error_message.value = self.trans.get_text('invalid_credentials', 'Invalid username or password.')
                self.error_message.color = ERROR_COLOR
            elif not user.get('is_active', True):
                self.error_message.value = self.trans.get_text('account_inactive', 'Your account is currently inactive.')
                self.error_message.color = ERROR_COLOR
            # في التطبيق الحقيقي، يجب عليك مقارنة الـ password_hash
            elif user.get('password_hash') != password: # للمحاكاة بدون مكتبة التشفير
                self.error_message.value = self.trans.get_text('invalid_credentials', 'Invalid username or password.')
                self.error_message.color = ERROR_COLOR
            else:
                self.error_message.value = ""
                self.error_message.color = ft.Colors.GREEN_700
                # نجاح الدخول: استدعاء الدالة الخارجية لتحويل الصفحة
                print(f"✅ تم تسجيل الدخول بنجاح للمستخدم: {username}")
                self.on_login_success(user)
                return

            self.error_message.update()
            
        except Exception as e:
            print(f"❌ خطأ في تسجيل الدخول: {e}")
            self.error_message.value = f"Login error: {e}"
            self.error_message.color = ERROR_COLOR
            self.error_message.update()

    # ---------------------------------
    # بناء واجهة المستخدم (Flet build method)
    # ---------------------------------
    def build(self):
        """بناء واجهة تسجيل الدخول."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    # رأس الصفحة
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.CALENDAR_MONTH, size=48, color=PRIMARY_COLOR),
                            ft.Text(
                                self.trans.get_text('app_title', 'Appointment Manager'),
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=PRIMARY_COLOR
                            ),
                            ft.Text(
                                self.trans.get_text('login_subtitle', 'Please sign in to continue'),
                                size=16,
                                color=ft.Colors.GREY_600
                            ),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20,
                        margin=ft.margin.only(bottom=20)
                    ),
                    
                    # حالة الترخيص
                    ft.Container(
                        content=ft.Row([
                            self.license_status_text,
                            self.license_button,
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=10,
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=8,
                        margin=ft.margin.only(bottom=20)
                    ),
                    
                    # نموذج تسجيل الدخول
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                self.username_field,
                                self.password_field,
                                self.login_button,
                                self.error_message,
                            ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=30,
                            width=400
                        ),
                        elevation=5,
                        margin=20
                    ),
                    
                    # تذييل الصفحة
                    ft.Container(
                        content=ft.Text(
                            self.trans.get_text('footer_text', 'Appointment Management System v1.0'),
                            size=12,
                            color=ft.Colors.GREY_500
                        ),
                        padding=20,
                        margin=ft.margin.only(top=20)
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            alignment=ft.alignment.center
        )