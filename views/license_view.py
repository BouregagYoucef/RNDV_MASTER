import flet as ft
from typing import Callable, Any, Optional, Dict
import os
import shutil
#from main import AppState 
from config.settings import LICENSE_FILE_PATH, PUBLIC_KEY_PATH, LICENSE_FILE_NAME
from datetime import datetime

class LicenseView(ft.Container):
    """
    واجهة تفعيل الترخيص: تعرض Machine ID وتسمح بتحميل ملف الترخيص.
    """
    
    def __init__(self, app_state, on_success: Callable[[Optional[Dict]], None]):
        super().__init__()
        self.app = app_state
        self.tr = app_state.tr
        self.on_activation_success = on_success
        self.current_machine_id = self.app.license.get_current_machine_id() # الحصول على ID الجهاز
        
        self.width = 500
        self.padding = 30
        self.bgcolor = self.app.theme.get('Surface_Cards', ft.Colors.WHITE)
        self.border_radius = 10
        
        
        # عناصر واجهة المستخدم
        self.machine_id_text = ft.Text(
            self.current_machine_id, 
            selectable=True, 
            size=12, 
            weight=ft.FontWeight.W_500
        )
        self.error_message = ft.Text("", color=self.app.theme.get('Error', ft.Colors.RED_500))
        self.success_message = ft.Text("", color=self.app.theme.get('Success', ft.Colors.GREEN_700))

        # 1. منتقي الملفات (File Picker)
        self.file_picker = ft.FilePicker(on_result=self._copy_license_file)

        # يجب أن تُضاف أداة FilePicker إلى الـ Page
        #self.app.db._conn.page.overlay.append(self.file_picker) # طريقة Flet لإضافة الـ Overlay
        #self.app.db._conn.page.update()
        #
        self.app.page.overlay.append(self.file_picker)
        self.app.page.update()

        self.content = self._build_ui()

    def _copy_license_file(self, e: ft.FilePickerResultEvent):
        """
        يتم استدعاؤها بعد اختيار ملف الترخيص.
        تقوم بنسخ الملف المختار إلى جذر التطبيق ثم تحاول التفعيل.
        """
        if e.files:
            selected_path = e.files[0].path
            
            # التأكد من أن الملف هو license.json
            if not selected_path.lower().endswith(LICENSE_FILE_NAME.lower()):
                self._show_message(self.tr.get_text('invalid_file', "الرجاء اختيار ملف 'license.json' صحيح."), is_error=True)
                return

            try:
                # 1. نسخ الملف إلى المسار المتوقع
                shutil.copy(selected_path, LICENSE_FILE_PATH)
                self._show_message(self.tr.get_text('file_copied', "تم نسخ الملف بنجاح. جاري محاولة التفعيل..."), is_error=False)
                self.update()
                
                # 2. محاولة التفعيل
                self._attempt_activation()

            except Exception as ex:
                self._show_message(f"{self.tr.get_text('copy_failed', 'فشل النسخ')}: {ex}", is_error=True)
                # تسجيل الحدث في Audit Logs
                self.app.db.execute_query(
                    "INSERT INTO Audit_Logs (timestamp, action_type, details) VALUES (?, ?, ?)",
                    (datetime.now().isoformat(), 'LICENSE_FAILED', f'File copy failed: {ex}'),
                    commit=True
                )
        else:
            self._show_message(self.tr.get_text('no_file_selected', "لم يتم اختيار أي ملف."), is_error=True)


    def _attempt_activation(self):
        """
        تستدعي منطق التحقق والتفعيل من LicenseManager.
        """
        is_activated = self.app.license.activate_from_file()

        if is_activated:
            self._show_message(self.tr.get_text('activation_success', "✅ تم التفعيل بنجاح! جاري التحويل..."), is_error=False)
            self.update()
            # استدعاء دالة النجاح لتوجيه المستخدم إلى صفحة الدخول (أو Dashboard)
            # نمرر None لأن التفعيل لا يتطلب بيانات مستخدم
            self.on_activation_success(None) 
        else:
            # استرداد رسالة الخطأ من جدول Licenses
            license_info = self.app.db.get_license_info()
            status_msg = license_info.get('signature_status', 'Unknown Error')
            
            error_details = self.tr.get_text('activation_failed', 'فشل التفعيل. السبب: ') + status_msg
            self._show_message(error_details, is_error=True)


    def _show_message(self, message: str, is_error: bool):
        """دالة مساعدة لعرض رسالة الخطأ أو النجاح."""
        if is_error:
            self.error_message.value = message
            self.success_message.value = ""
        else:
            self.success_message.value = message
            self.error_message.value = ""
        self.update()

    def _build_ui(self):
        """بناء تخطيط واجهة المستخدم Flet."""
        
        # زر نسخ مُعرِّف الجهاز
        copy_button = ft.IconButton(
            icon=ft.Icons.CONTENT_COPY_OUTLINED,
            tooltip=self.tr.get_text('copy_id', "نسخ مُعرِّف الجهاز"),
            on_click=lambda e: e.page.set_clipboard(self.current_machine_id)
        )
        
        # زر اختيار ملف الترخيص
        select_file_button = ft.ElevatedButton(
            text=self.tr.get_text('select_license', "اختيار ملف الترخيص (license.json)"),
            icon=ft.Icons.FILE_OPEN,
            on_click=lambda e: self.file_picker.pick_files(
                dialog_title=self.tr.get_text('select_license_file', "اختر ملف الترخيص"),
                allow_multiple=False,
                allowed_extensions=['json']
            )
        )

        return ft.Column(
            controls=[
                ft.Text(self.tr.get_text('activation_title', "🔑 تفعيل البرنامج"), size=26, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                
                ft.Text(self.tr.get_text('step1_title', "الخطوة 1: أرسل مُعرِّف الجهاز"), size=14, weight=ft.FontWeight.BOLD),
                ft.Row(
                    controls=[
                        self.machine_id_text,
                        copy_button
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),

                ft.Text(self.tr.get_text('step2_title', "الخطوة 2: تحميل ملف الترخيص المُرسل إليك"), size=14, weight=ft.FontWeight.BOLD),
                select_file_button,

                ft.Divider(height=20),
                self.error_message,
                self.success_message,
                
                ft.Text(self.tr.get_text('note_msg', "ملاحظة: ضع ملف الترخيص المُرسل في نفس مجلد البرنامج ثم اضغط 'اختيار'.") , size=10, color=ft.Colors.BLACK54)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        )
