from functools import lru_cache
import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Tuple, Any, Optional

# تعريف مسار قاعدة البيانات
DB_NAME = 'appointment_manager.db'
DB_PATH = ""#os.path.join(os.path.dirname(__file__), DB_NAME)
# --- تعريف أوامر SQL لإنشاء الجداول ---
SCHEMA_SQL = ["""
PRAGMA foreign_keys = ON;
""",
"""
CREATE TABLE IF NOT EXISTS "Settings" (
	"id" INTEGER PRIMARY KEY,
	"company_name" VARCHAR,
	"language" VARCHAR,
	"logo_path" VARCHAR,
	"working_days" VARCHAR,
	"start_time" TEXT, -- TEXT for TIME format (HH:MM)
	"end_time" TEXT,    -- TEXT for TIME format (HH:MM)
	"phone_numbers" VARCHAR,
	"emails" VARCHAR,
	"hardware_id" VARCHAR NOT NULL UNIQUE
);""",

""" 

CREATE TABLE IF NOT EXISTS "Users" (
	"user_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"username" VARCHAR NOT NULL UNIQUE,
	"password_hash" VARCHAR NOT NULL,
	"full_name" VARCHAR,
	"is_active" BOOLEAN DEFAULT 1 ,-- SQLite uses 1 for True, 0 for False
    "role" VARCHAR DEFAULT 'receptionist'
);""",

""" 

CREATE TABLE IF NOT EXISTS "Clients" (
	"client_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"full_name" VARCHAR NOT NULL,
	"phone_number" VARCHAR UNIQUE,
	"email" VARCHAR,
	"notes" TEXT,
	"created_at" TEXT -- TEXT for TIMESTAMP (ISO8601)
);""",

""" 

CREATE TABLE IF NOT EXISTS "Services" (
	"service_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"name_ar" VARCHAR NOT NULL,
	"name_fr" VARCHAR,
	"price" REAL DEFAULT 0.0,
	"duration_minutes" INTEGER,
	"is_active" BOOLEAN DEFAULT 1
);""",

""" 

CREATE TABLE IF NOT EXISTS "Appointments" (
	"appointment_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"client_id" INTEGER NOT NULL,
	"user_id" INTEGER NOT NULL,
	"service_id" INTEGER,
	"date" TEXT NOT NULL, -- TEXT for DATE (YYYY-MM-DD)
	"start_time" TEXT NOT NULL, -- TEXT for TIME (HH:MM)
	"duration_minutes" INTEGER,
	"status" VARCHAR NOT NULL,
	"notes" VARCHAR,
	"is_paid" BOOLEAN DEFAULT 0,
	"reminder_set" BOOLEAN DEFAULT 0,
	"created_at" TEXT,
	"updated_at" TEXT,
	FOREIGN KEY ("client_id") REFERENCES "Clients"("client_id")
	ON UPDATE NO ACTION ON DELETE NO ACTION,
	FOREIGN KEY ("user_id") REFERENCES "Users"("user_id")
	ON UPDATE NO ACTION ON DELETE NO ACTION,
	FOREIGN KEY ("service_id") REFERENCES "Services"("service_id")
	ON UPDATE NO ACTION ON DELETE NO ACTION
);""",

""" 

CREATE TABLE IF NOT EXISTS "Translations" (
	"translation_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"key" VARCHAR NOT NULL UNIQUE,
	"ar" TEXT,
	"fr" TEXT,
    "en" TEXT
);""",

""" 

CREATE TABLE IF NOT EXISTS "Device_Info" (
	"id" INTEGER PRIMARY KEY,
	"machine_id_hash" VARCHAR NOT NULL UNIQUE,
	"bios_uuid" VARCHAR,
	"disk_serial" VARCHAR,
	"mac_address" VARCHAR
);""",

""" 

CREATE TABLE IF NOT EXISTS "Licenses" (
	"id" INTEGER PRIMARY KEY,
	"license_key" VARCHAR NOT NULL default 'N/A',
	"is_active" BOOLEAN DEFAULT 0,
	"machine_id_used" VARCHAR,
	"issued_at" TEXT,
	"expires_at" TEXT,
	"signature_status" VARCHAR,
	"last_check_date" TEXT
);""",

"""
CREATE TABLE IF NOT EXISTS "Audit_Logs" (
	"log_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"user_id" INTEGER,
	"timestamp" TEXT NOT NULL,
	"action_type" VARCHAR NOT NULL,
	"details" VARCHAR,
	"related_data" VARCHAR,
	FOREIGN KEY ("user_id") REFERENCES "Users"("user_id")
	ON UPDATE NO ACTION ON DELETE NO ACTION
);""",

""" 

CREATE TABLE IF NOT EXISTS "Invoices" (
	"invoice_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"invoice_number" INTEGER NOT NULL UNIQUE AUTOINCREMENT,
	"appointment_id" INTEGER NOT NULL UNIQUE,
	"created_by_user_id" INTEGER NOT NULL,
	"issue_date" TEXT NOT NULL,
	"total_amount" REAL DEFAULT 0.0,
	"payment_status" VARCHAR NOT NULL,
	FOREIGN KEY ("appointment_id") REFERENCES "Appointments"("appointment_id")
	ON UPDATE NO ACTION ON DELETE NO ACTION,
	FOREIGN KEY ("created_by_user_id") REFERENCES "Users"("user_id")
	ON UPDATE NO ACTION ON DELETE NO ACTION
);""",
"""
CREATE TABLE IF NOT EXISTS "theme" (
	"theme_id" INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	"theme_name" VARCHAR,
	"settings_id" INTEGER,
	"state" VARCHAR DEFAULT 'active',
	"is_default" BOOLEAN DEFAULT 0,
	FOREIGN KEY ("settings_id") REFERENCES "Settings"("id")
	ON UPDATE NO ACTION ON DELETE NO ACTION
);""",
"""
CREATE TABLE IF NOT EXISTS "theme_details" (
	"id" INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	"category" VARCHAR,
	"subcategory" VARCHAR,
	"element_name" VARCHAR,
	"property_name" VARCHAR,
	"property_value" VARCHAR,
	"language" VARCHAR,
	"font_weight" VARCHAR,
	"font_size" VARCHAR,
	"created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
	"theme_id" INTEGER NOT NULL,
	FOREIGN KEY ("theme_id") REFERENCES "theme"("theme_id")
	ON UPDATE CASCADE ON DELETE CASCADE
);
"""
]


# إدخال بيانات مفاتيح الترجمة   
translations_keys = """
INSERT INTO "Translations" ("key", "ar", "fr", "en") VALUES
-- --- نصوص عامة ---
('app_title', 'نظام إدارة المواعيد', 'Système de Rendez-vous', 'Appointment Manager'),
('welcome_msg', 'أهلاً بك', 'Bienvenue', 'Welcome'),

-- --- نصوص شاشة الترخيص (LicenseView) ---
('activation_title', '🔑 تفعيل البرنامج', 'Activation du Programme', '🔑 Program Activation'),
('step1_title', 'الخطوة 1: أرسل مُعرِّف الجهاز', 'Étape 1: Envoyez l''ID Machine', 'Step 1: Send Machine ID'),
('copy_id', 'نسخ مُعرِّف الجهاز', 'Copier l''ID Machine', 'Copy Machine ID'),
('step2_title', 'الخطوة 2: تحميل ملف الترخيص', 'Étape 2: Téléversez le fichier Licence', 'Step 2: Upload License File'),
('select_license', 'اختيار ملف الترخيص', 'Choisir le Fichier Licence', 'Select License File'),
('select_license_file', 'اختر ملف الترخيص', 'Sélectionnez Fichier Licence', 'Select License File'),
('note_msg', 'ملاحظة: ضع ملف الترخيص المرسل في مجلد البرنامج ثم اضغط "اختيار".', 'Note: Placez le fichier dans le dossier de l''application.', 'Note: Place the file in the app folder then select it.'),
('activation_success', '✅ تم التفعيل بنجاح! جاري التحويل...', 'Activation réussie !', '✅ Activation successful! Redirecting...'),
('activation_failed', '❌ فشل التفعيل. السبب: ', 'Échec de l''activation. Raison: ', '❌ Activation failed. Reason: '),
('invalid_file', 'الرجاء اختيار ملف ''license.json'' صحيح.', 'Veuillez sélectionner un fichier valide.', 'Please select a valid ''license.json'' file.'),
('file_copied', 'تم نسخ الملف بنجاح. جاري محاولة التفعيل...', 'Fichier copié. Tentative d''activation...', 'File copied. Attempting activation...'),
('no_file_selected', 'لم يتم اختيار أي ملف.', 'Aucun fichier sélectionné.', 'No file selected.'),
('copy_failed', 'فشل نسخ الملف.', 'Échec de la copie du fichier.', 'File copy failed.'),

-- --- نصوص شاشة تسجيل الدخول (LoginView) ---
('login_title', 'تسجيل دخول موظف الاستقبال', 'Connexion Réceptionniste', 'Receptionist Login'),
('username_label', 'اسم المستخدم', 'Nom d''utilisateur', 'Username'),
('password_label', 'كلمة المرور', 'Mot de passe', 'Password'),
('login_button', 'تسجيل الدخول', 'Se Connecter', 'Log In'),
('empty_fields', 'الرجاء إدخال اسم المستخدم وكلمة المرور.', 'Veuillez remplir tous les champs.', 'Please fill in all fields.'),
('wrong_password', 'كلمة المرور خاطئة.', 'Mot de passe incorrect.', 'Wrong password.'),
('user_not_found', 'اسم المستخدم غير موجود.', 'Utilisateur non trouvé.', 'User not found.'),
('version', 'الإصدار', 'Version', 'Version'),

-- --- نصوص لوحة التحكم والإعدادات العامة (Dashboard / General) ---
('dashboard_title', 'لوحة التحكم', 'Tableau de Bord', 'Dashboard'),
('appointments_tab', 'المواعيد', 'Rendez-vous', 'Appointments'),
('clients_tab', 'العملاء', 'Clients', 'Clients'),
('reports_tab', 'التقارير', 'Rapports', 'Reports'),
('settings_tab', 'الإعدادات', 'Paramètres', 'Settings'),
('logout_btn', 'تسجيل الخروج', 'Déconnexion', 'Log Out'),

-- --- نصوص إدارة المواعيد ---
('new_appointment', 'موعد جديد', 'Nouveau Rendez-vous', 'New Appointment'),
('date_label', 'التاريخ', 'Date', 'Date'),
('time_label', 'الوقت', 'Heure', 'Time'),
('duration_label', 'المدة (بالدقائق)', 'Durée (min)', 'Duration (min)'),
('service_label', 'الخدمة / الغرض', 'Service / Objet', 'Service / Purpose'),
('status_label', 'الحالة', 'Statut', 'Status'),
('status_confirmed', 'مُؤكَّد', 'Confirmé', 'Confirmed'),
('status_attended', 'حاضر', 'Présent', 'Attended'),
('status_absent', 'غائب', 'Absent', 'Absent'),
('status_cancelled', 'مُلغى', 'Annulé', 'Cancelled'),
('save_btn', 'حفظ', 'Enregistrer', 'Save'),
('cancel_btn', 'إلغاء', 'Annuler', 'Cancel'),

-- --- نصوص التقارير ---
('report_daily', 'التقرير اليومي', 'Rapport Journalier', 'Daily Report'),
('report_weekly', 'التقرير الأسبوعي', 'Rapport Hebdomadaire', 'Weekly Report'),
('report_monthly', 'التقرير الشهري', 'Rapport Mensuel', 'Monthly Report'),
('stats_attendance', 'نسبة الحضور', 'Taux de Présence', 'Attendance Rate'),
('stats_peak_hours', 'ساعات الذروة', 'Heures de Pointe', 'Peak Hours'),
('print_btn', 'طباعة', 'Imprimer', 'Print'),

-- --- نصوص الإعدادات ---
('settings_company_info', 'معلومات الشركة', 'Infos Société', 'Company Info'),
('settings_theme', 'مظهر التطبيق', 'Thème de l''App', 'App Theme'),
('settings_working_hours', 'ساعات العمل', 'Heures de Travail', 'Working Hours'),
('language_select', 'اللغة', 'Langue', 'Language');
"""



#set theme default values
default_theme_values = {""" 
INSERT INTO theme (theme_name, settings_id, state, is_default) VALUES 
('default_theme', 1, 'active', 1);
""",
"""
INSERT INTO theme_details (theme_id, category, subcategory, element_name, property_name, property_value) VALUES
-- إدخال بيانات الألوان
(1, 'color', 'primary', 'blue_trust', 'hex', '#2E86AB'),
(1, 'color', 'primary', 'pure_white', 'hex', '#FFFFFF'),
(1, 'color', 'primary', 'charcoal_black', 'hex', '#2A2D34'),
(1, 'color', 'secondary', 'light_blue', 'hex', '#6BBAD6'),
(1, 'color', 'secondary', 'light_gray', 'hex', '#F8F9FA'),
(1, 'color', 'secondary', 'medium_gray', 'hex', '#E9ECEF'),
(1, 'color', 'status', 'success_green', 'hex', '#4CAF50'),
(1, 'color', 'status', 'warning_orange', 'hex', '#FF9800'),
(1, 'color', 'status', 'danger_red', 'hex', '#F44336');
""",

"""
INSERT INTO theme_details (theme_id, category, subcategory, element_name, property_name, property_value, language, font_weight, font_size) VALUES
-- إدخال بيانات الطباعة العربية
(1, 'typography', 'main_title', 'arabic_main_title', 'font_family', 'IBM Plex Sans Arabic', 'ar', 'Bold', '24px'),
(1, 'typography', 'subtitle', 'arabic_subtitle', 'font_family', 'IBM Plex Sans Arabic', 'ar', 'SemiBold', '18px'),
(1, 'typography', 'normal_text', 'arabic_normal', 'font_family', 'IBM Plex Sans Arabic', 'ar', 'Regular', '16px'),
(1, 'typography', 'secondary_text', 'arabic_secondary', 'font_family', 'IBM Plex Sans Arabic', 'ar', 'Light', '14px');
 """,
 
"""
INSERT INTO theme_details (theme_id, category, subcategory, element_name, property_name, property_value, language, font_weight, font_size) VALUES
-- إدخال بيانات الطباعة الإنجليزية
(1, 'typography', 'main_title', 'english_main_title', 'font_family', 'Inter', 'en', 'Bold', '24px'),
(1, 'typography', 'subtitle', 'english_subtitle', 'font_family', 'Inter', 'en', 'SemiBold', '18px'),
(1, 'typography', 'normal_text', 'english_normal', 'font_family', 'Inter', 'en', 'Regular', '16px'),
(1, 'typography', 'secondary_text', 'english_secondary', 'font_family', 'Inter', 'en', 'Light', '14px');
""",
""" 
INSERT INTO theme_details (theme_id, category, subcategory, element_name, property_name, property_value) VALUES
-- إدخال بيانات الأزرار
(1, 'button', 'primary', 'primary_button', 'background', '#2E86AB'),
(1, 'button', 'primary', 'primary_button', 'text_color', '#FFFFFF'),
(1, 'button', 'primary', 'primary_button', 'border_radius', '8px'),
(1, 'button', 'primary', 'primary_button', 'box_shadow', '0px 2px 4px rgba(46, 134, 171, 0.2)'),
(1, 'button', 'secondary', 'secondary_button', 'background', 'transparent'),
(1, 'button', 'secondary', 'secondary_button', 'border', '1px solid #2E86AB'),
(1, 'button', 'secondary', 'secondary_button', 'text_color', '#2E86AB'),
(1, 'button', 'secondary', 'secondary_button', 'border_radius', '8px'),
(1, 'button', 'hover', 'button_hover', 'box_shadow', '0px 4px 8px rgba(46, 134, 171, 0.3)'),
(1, 'button', 'hover', 'button_hover', 'transform', 'translateY(-1px)');
""",
""" 
INSERT INTO theme_details (theme_id, category, subcategory, element_name, property_name, property_value) VALUES
-- إدخال بيانات الحقول والنماذج
(1, 'form', 'input', 'input_field', 'background', '#FFFFFF'),
(1, 'form', 'input', 'input_field', 'border', '1px solid #E9ECEF'),
(1, 'form', 'input', 'input_field', 'border_radius', '6px'),
(1, 'form', 'input', 'input_field', 'box_shadow', '0px 0px 0px 2px rgba(46, 134, 171, 0.1)'),
(1, 'form', 'focus', 'input_focus', 'border', '1px solid #2E86AB'),
(1, 'form', 'focus', 'input_focus', 'box_shadow', '0px 0px 0px 3px rgba(46, 134, 171, 0.15)');
""",
""" 
INSERT INTO theme_details (theme_id, category, subcategory, element_name, property_name, property_value) VALUES
-- إدخال بيانات الأيقونات
(1, 'icon', 'style', 'line_icons', 'type', 'Line Icons'),
(1, 'icon', 'style', 'line_icons', 'stroke_width', '1.5px'),
(1, 'icon', 'size', 'main_icons', 'size', '20px'),
(1, 'icon', 'size', 'secondary_icons', 'size', '16px'),
(1, 'icon', 'color', 'icon_default', 'color', '#2A2D34'),
(1, 'icon', 'color', 'icon_active', 'color', '#6BBAD6');""",

"""
INSERT INTO theme_details (theme_id, category, subcategory, element_name, property_name, property_value) VALUES
-- إدخال بيانات التقويم
(1, 'calendar', 'current_day', 'current_day', 'background', '#2E86AB'),
(1, 'calendar', 'current_day', 'current_day','text_color', '#FFFFFF'),
(1, 'calendar', 'selected_day', 'selected_day', 'background', '#6BBAD6'),
(1, 'calendar', 'selected_day', 'selected_day', 'text_color', '#FFFFFF'),
(1, 'calendar', 'normal_day', 'normal_day', 'background', '#FFFFFF'),
(1, 'calendar', 'normal_day', 'normal_day', 'text_color', '#2A2D34'),
(1, 'calendar', 'appointment', 'confirmed', 'border_color', '#4CAF50'),
(1, 'calendar', 'appointment', 'pending', 'border_color', '#FF9800'),
(1, 'calendar', 'appointment', 'cancelled', 'border_color', '#E9ECEF'),
(1, 'calendar', 'appointment', 'cancelled', 'text_decoration', 'line-through'); """,
"""
INSERT INTO theme_details (theme_id, category, subcategory, element_name, property_name, property_value) VALUES
-- إدخال بيانات الرسوم المتحركة
(1, 'animation', 'timing', 'default', 'duration', '0.3s'),
(1, 'animation', 'timing', 'default', 'timing_function', 'ease-out'),
(1, 'animation', 'types', 'animations', 'list', 'fade-in, slide-up, scale'); """,
""" 
INSERT INTO theme_details (theme_id, category, subcategory, element_name, property_name, property_value) VALUES
-- إدخال بيانات التباعد
(1, 'spacing', 'scale', 'base_unit', 'size', '8px'),
(1, 'spacing', 'sizes', 'small', 'size', '8px'),
(1, 'spacing', 'sizes', 'medium', 'size', '16px'),
(1, 'spacing', 'sizes', 'large', 'size', '24px'),
(1, 'spacing', 'sizes', 'xlarge', 'size', '32px');"""
}
                        
# إدخال بيانات الألوان

class DatabaseManager:
    """
    مدير قاعدة البيانات: مسؤول عن الاتصال بقاعدة البيانات وتنفيذ جميع عمليات CRUD والتقارير.
"""

    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        self._conn = None
        self._cursor = None
        self._current_theme_cache = None
        self._current_theme_id = None
        self.initialize_db()

    def _connect(self):
        try:
            """إنشاء اتصال بقاعدة البيانات"""
            if self._conn is None:
                self._conn = sqlite3.connect(self.db_path)
                self._conn.row_factory = sqlite3.Row  # للوصول إلى الأعمدة بالاسم
                self._cursor = self._conn.cursor()
                print(f"DBM ✅ Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            print(f"DBM ❌  Database Connection Error: {e}")
            return None
        
    
    def _close(self):
        try:
            """إغلاق الاتصال بقاعدة البيانات"""
            if self._conn:
                self._conn.close()
                self._conn = None
                self._cursor = None
                print("DBM ❌ Connection closed")
        except sqlite3.Error as e:
            print(f"DBM ❌ Database Closing Error: {e}")
            return None
        
    def execute_query(self, query: str, params: Optional[Tuple] = None, fetch_one: bool = False, commit: bool = False) -> Any:
        """دالة عامة لتنفيذ الاستعلامات"""
        self._connect()
        print(f"\n\n = ========DBM ⚙️ Executing query in table: {query[0:50]}  ")
        try:
            if params is None:
                params = ()
            self._cursor.execute(query, params)
            print(f"DBM ⚙️ Executed query: ")
            if commit:
                self._conn.commit()
                # إرجاع معرّف آخر إدخال (لعمليات INSERT)
                print("DBM commit 💾 Changes committed to the database.")
                return self._cursor.lastrowid
            
            if fetch_one:
                print("DBM fetch_one 📥 Fetching one record.")
                return self._cursor.fetchone()
            else:
                print("DBM fetch_all 📥 Fetching all records.")
                return self._cursor.fetchall()
        
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            print(f"DBM except❗ Failed query: {query} | Params: {params}")
            return None
        finally:
            print(f"DBM finally❗ db close called.")
            self._close()
            print(f"=========DBM ⚙️ Query execution completed.\n\n")
    
    
    def initialize_db(self):
        """إنشاء الجداول إذا لم تكن موجودة"""
        print("\n\n\n=========== DBM ⚙️ Initializing database schema... ==========")
        try:
            for i, schema in enumerate(SCHEMA_SQL):
                self.execute_query(schema)
                print(f"DBM ⚙️ Executed schema {i+1}/{len(SCHEMA_SQL)}")
            self.set_default_settings()
            self.set_default_license_info()
        except Exception as e:
            print(f"Error initializing database: {e}")
        print("=========== DBM ✅ Database schema initialized. ==========\n\n")

        try: 
            #check if default translation keys exist, if not insert them
            existing_keys = self.execute_query("SELECT COUNT(*) as count FROM Translations")
            if existing_keys and existing_keys[0]['count'] == 0:
                self.execute_query(translations_keys, commit=True)
                print("DBM ✅  Default translation keys ensured.")

            #and if default theme values not exist insert them
            if not self.get_default_theme():
                for i in default_theme_values:
                    self.execute_query(i, commit=True)
                    print("DBM ✅  Default translation keys and theme values ensured.")

        except Exception as e:
            print(f"DBM ❌ Error inserting default translation keys or theme values: {e}")




# ----------------------------------------------------------------------
# 1. دوال الإعدادات والتراخيص (Settings & Licensing)
# ----------------------------------------------------------------------

    def set_default_settings(self):
        """إنشاء سجل إعدادات افتراضي إذا لم يكن موجودًا"""
        try:
            """إنشاء سجل إعدادات افتراضي إذا كان الجدول فارغًا"""
            query = "INSERT INTO Settings (id, company_name, language,hardware_id) VALUES (1, 'Appointment Manager', 'ar', 'dummy_hardware_id')"
            self.execute_query(query, commit=True)
            print("DBM ✅  Default settings ensured.")
        except Exception as e:
            print(f"DBM ❌ Error setting default settings: {e}")

    def get_settings(self) -> Optional[Dict]:
        """استرداد جميع الإعدادات
        Args:
            None
        Returns:
            Optional[Dict]: {'id': 1, 'company_name': 'Appointment Manager', 'language': 'ar','logo_path': 'path','working_days': 'Saturday, Sunday','start_time': '09:00','end_time': '17:00','phone_numbers': '123456789','emails': 'info@example.com','hardware_id': 'dummy_hardware_id'}
              قاموس يحتوي على إعدادات التطبيق أو None إذا لم توجد
        """

        try:
            query = "SELECT * FROM Settings"
            result = self.execute_query(query, fetch_one=True)
            print(f"DBM ⚙️ Retrieved settings: {result}")
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getter settings retrieving settings: {e}")
            return None
    
    def update_settings(self, data: Dict) -> bool:
        """تحديث الإعدادات
        Args:
            data (Dict): قاموس يحتوي على الحقول التي سيتم تحديثها، e.g., {'company_name': 'Appointment Manager', 'language': 'ar','logo_path': 'path','working_days': 'Saturday, Sunday','start_time': '09:00','end_time': '17:00','phone_numbers': '123456789','emails': 'info@example.com','hardware_id': 'dummy_hardware_id'}
        Returns:
            bool: True إذا تم التحديث بنجاح، False خلاف ذلك.
        """
        try:
            """تحديث حقول الإعدادات (Setters)"""
            # بناء جزء SET من الاستعلام ديناميكياً
            set_parts = [f"{k} = ?" for k in data.keys() if k != 'id']
            values = list(data.values())

            query = f"UPDATE Settings SET {', '.join(set_parts)} WHERE id = 1"
            return self.execute_query(query, tuple(values), commit=True) is not None
        except Exception as e:
            print(f"DBM ❌ Error setter settings updating settings: {e}")
            return False
        
    def set_device_info(self, data: Dict) -> bool:
        """إدخال/تحديث معلومات الجهاز (Setter)
        Args:
            data (Dict): قاموس يحتوي على معلومات الجهاز، e.g., {'machine_id_hash': 'hash_value', 'bios_uuid': 'uuid_value', 'disk_serial': 'serial_value', 'mac_address': 'mac_value'}
        Returns:
            bool: True إذا تم التحديث بنجاح، False خلاف ذلك.
        """

        try:
            # يتم استخدام INSERT OR REPLACE لضمان وجود سجل واحد فقط (بسبب قيد UNIQUE)
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT OR REPLACE INTO Device_Info (id, {keys}) VALUES (1, {placeholders})"
            return self.execute_query(query, values, commit=True) is not None
        except Exception as e:
            print(f"DBM ❌ Error setter device info setting device info: {e}")
            return False
        
    def get_device_info(self) -> Optional[Dict]:
        """استرداد معلومات الجهاز (Getter)
        Args:
            None
        Returns:
            Optional[Dict]:{'id': 1, 'machine_id_hash': 'hash_value', 'bios_uuid': 'uuid_value', 'disk_serial': 'serial_value', 'mac_address': 'mac_value'}
              قاموس يحتوي على معلومات الجهاز، أو None إذا لم يتم العثور على سجل.
        """
        try:
            query = "SELECT * FROM Device_Info WHERE id = 1"
            result = self.execute_query(query, fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getter device info retrieving device info: {e}")
            return None
        
    def set_license_info(self, data: Dict) -> bool:
        """إدخال/تحديث معلومات الترخيص
        Args:
            data (Dict): قاموس يحتوي على معلومات الترخيص، e.g., {'license_key': 'key_value', 'is_active': 1, 'machine_id_used': 'machine_id', 'issued_at': '2024-01-01', 'expires_at': '2025-01-01', 'signature_status': 'valid', 'last_check_date': '2024-06-01'}
        Returns:
            bool: True إذا تم التحديث بنجاح، False خلاف ذلك.
        """

        try:
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT OR REPLACE INTO Licenses (id, {keys}) VALUES (1, {placeholders})"
            return self.execute_query(query, values, commit=True) is not None
        except Exception as e:
            print(f"DBM ❌ Error setter license setting license info: {e}")
            return False
    
    def get_license_info(self) -> Optional[Dict]:
        """استرداد معلومات الترخيص
        Args:
            None
        Returns:
            Optional[Dict]:{'id': 1, 'license_key': 'key_value', 'is_active': 1, 'machine_id_used': 'machine_id', 'issued_at': '2024-01-01', 'expires_at': '2025-01-01', 'signature_status': 'valid', 'last_check_date': '2024-06-01'}
              قاموس يحتوي على معلومات الترخيص، أو None إذا لم يتم العثور على سجل.
        """
        try:
            query = "SELECT * FROM Licenses WHERE id = 1"
            result = self.execute_query(query, fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getter license retrieving license info: {e}")
            return None

    def set_default_license_info(self):
        """إنشاء سجل ترخيص افتراضي إذا كان الجدول فارغًا"""
        try:
            query = "INSERT OR IGNORE INTO Licenses (id, is_active) VALUES (1, 0)"
            self.execute_query(query, commit=True)
        except Exception as e:
            print(f"DBM ❌ Error setting default license info: {e}")
            return False
# أضف هذه الدوال في القسم الخاص بـ "دوال الإعدادات والتراخيص" في DatabaseManager


#=========== theme management functions ===========

    #============= theme ==============
    def add_theme(self, data: dict) -> bool:
        """
        إدخال ثيم جديد
        
        Args:
            data (dict): {'theme_name': 'Dark Theme', 'settings_id': 1, 'state': 'active', 'is_default': 0}
        
        Returns:
            bool: True إذا تم الإدخال بنجاح، False خلاف ذلك.
        """
        try:
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT INTO theme ({keys}) VALUES ({placeholders})"
            return self.execute_query(query, values, commit=True) is not None
        except Exception as e:
            print(f"❌ Error inserting theme: {e}")
            return False

    def get_default_theme(self) -> Optional[int]:
        """
        الحصول على معرف الثيم الافتراضي
        Args:
            None
        Returns:
            Optional[int]: معرف الثيم الافتراضي أو None إذا لم يكن موجودًا.
        
        """
        try:
            query = "SELECT theme_id FROM theme WHERE is_default = 1 AND state = 'active' LIMIT 1"
            result = self.execute_query(query)
            return result[0]['theme_id'] if result else None
        except Exception as e:
            print(f"❌ Error getting default theme: {e}")
            return None

    def get_last_theme(self) -> Optional[int]:
        """
        الحصول على معرف آخر ثيم تم إدخاله
        Args:
            None
        Returns:
            Optional[int]: معرف آخر ثيم تم إدخاله أو None إذا لم يكن موجودًا.
        
        """
        try:
            query = "SELECT theme_id FROM theme ORDER BY ROWID DESC LIMIT 1"
            result = self.execute_query(query)
            return result if result else None
        except Exception as e :
            print(f"DBM ❌ Error getting the last theme id : {e}")
            return None

    def set_default_theme(self, theme_id: int) -> bool:
        """
        تعيين ثيم كافتراضي
        Args:
            theme_id (int): معرف الثيم الذي سيتم تعيينه كافتراضي.
        
        Returns:
            bool: True إذا تم التعيين بنجاح، False خلاف ذلك.
        """
        try:
            # أولاً، إعادة تعيين الثيم الافتراضي الحالي
            reset_query = "UPDATE theme SET is_default = 0 WHERE is_default = 1"
            self.execute_query(reset_query, commit=True)
            
            # ثم تعيين الثيم الجديد كافتراضي
            set_query = "UPDATE theme SET is_default = 1 WHERE theme_id = ?"
            return self.execute_query(set_query, (theme_id,), commit=True) is not None
        except Exception as e:
            print(f"❌ Error setting default theme: {e}")
            return False
    
    def update_theme_settings(self, data: Dict) -> bool:
        """
        تحديث إعدادات التنسيق (Setter)

        Args:
            data (Dict): قاموس يحتوي على الحقول التي سيتم تحديثها، مثل {'theme_name': 'Dark Theme', 'state': 'active', 'is_default': 0}
        Returns:
            bool: True إذا تم التحديث بنجاح، False خلاف ذلك.
        
        """
        try:
            if not data:
                return False

            # بناء جزء SET من الاستعلام ديناميكياً
            set_parts = [f"{k} = ?" for k in data.keys() if k != 'id']
            values = list(data.values())

            query = f"UPDATE theme SET {', '.join(set_parts)} WHERE id = 1"
            return self.execute_query(query, tuple(values), commit=True) is not None
        except Exception as e:
            print(f"DBM ❌ Error setter theme updating theme settings: {e}")
            return False
    #=========== theme elements ==========
    @lru_cache(maxsize=10)
    def get_theme_data(self, theme_id: Optional[int] = None) -> Dict[str, Dict]:
        """استرداد بيانات الثيم مع caching"""
        try:
            if theme_id is None:
                theme_id = self.get_default_theme()
                if theme_id is None:
                    return {}
            
            query = """
            SELECT td.category, td.subcategory, td.element_name, 
                   td.property_name, td.property_value, td.language,
                   td.font_weight, td.font_size, t.theme_name
            FROM theme_details td
            JOIN theme t ON td.theme_id = t.theme_id
            WHERE td.theme_id = ?
            """
            results = self.execute_query(query, (theme_id,))
            
            if not results:
                return {}
            
            organized_theme = self._organize_theme_data(results)
            self._current_theme_cache = organized_theme
            self._current_theme_id = theme_id
            
            return organized_theme
            
        except Exception as e:
            print(f"❌ Error retrieving theme data: {e}")
            return {}
    
    def _organize_theme_data(self, results: List) -> Dict[str, Dict]:
        """تنظيم بيانات الثيم في هيكل هرمي"""
        theme_dict = {}
        
        for row in results:
            row_dict = dict(row)
            category = row_dict['category']
            subcategory = row_dict['subcategory']
            element_name = row_dict['element_name']
            property_name = row_dict['property_name']
            property_value = row_dict['property_value']
            language = row_dict['language']
            
            # بناء الهيكل الهرمي
            if category not in theme_dict:
                theme_dict[category] = {}
            
            if subcategory:
                if subcategory not in theme_dict[category]:
                    theme_dict[category][subcategory] = {}
                
                key = f"{element_name}_{language}" if language else element_name
                
                if key not in theme_dict[category][subcategory]:
                    theme_dict[category][subcategory][key] = {
                        'property_value': property_value,
                        'font_weight': row_dict.get('font_weight'),
                        'font_size': row_dict.get('font_size')
                    }
                else:
                    theme_dict[category][subcategory][key][property_name] = property_value
            else:
                if element_name not in theme_dict[category]:
                    theme_dict[category][element_name] = {}
                
                theme_dict[category][element_name][property_name] = property_value
        
        return theme_dict
    
    def get_current_theme(self) -> Dict[str, Dict]:
        """الحصول على الثيم الحالي (مع caching)
        Returns:
            Dict[str, Dict]: قاموس يحتوي على بيانات الثيم الحالي.
        """
        if self._current_theme_cache is None:
            self._current_theme_cache = self.get_theme_data()
        return self._current_theme_cache

    def get_theme_by_category(self, category: str) -> Dict:
        """استرداد إعدادات فئة محددة
        Args:
            category (str): الفئة التي سيتم استردادها (مثل 'color', 'typography', 'button').
        Returns:
            Dict: قاموس يحتوي على إعدادات الفئة المحددة.
        """
        theme_data = self.get_current_theme()
        return theme_data.get(category, {})
    
    def get_color(self, color_name: str) -> str:
        """استرداد لون محدد بسهولة
        Args:
            color_name (str): اسم اللون الذي سيتم استرداده (مثل 'blue_trust', 'pure_white').
        Returns:
            str: قيمة اللون (مثل '#2E86AB') أو سلسلة فارغة إذا لم يتم العثور عليه.
        """
        colors = self.get_theme_by_category('color')
        for subcategory in colors.values():
            for element_name, properties in subcategory.items():
                if color_name in element_name and 'property_value' in properties:
                    return properties['property_value']
        return ''
    
    def get_font_style(self, language: str, font_type: str) -> Dict:
        """استرداد إعدادات الخط
        Args:
            language (str): اللغة (مثل 'ar' أو 'en').
            font_type (str): نوع الخط (مثل 'main_title', 'subtitle', 'normal', 'secondary').
        Returns:
            Dict: قاموس يحتوي على إعدادات الخط (مثل {'font_family': 'IBM Plex Sans Arabic', 'font_weight': 'Bold', 'font_size': '24px'}) أو قاموس فارغ إذا لم يتم العثور عليه.
        """
        typography = self.get_theme_by_category('typography')
        search_key = f"{font_type}_{language}"
        
        for subcategory in typography.values():
            for element_name, properties in subcategory.items():
                if search_key in element_name:
                    return {
                        'font_family': properties.get('property_value', ''),
                        'font_weight': properties.get('font_weight', ''),
                        'font_size': properties.get('font_size', '')
                    }
        return {}
    
    def export_theme_to_json(self, theme_id: Optional[int] = None, file_path: str = "theme_export.json") -> bool:
        """تصدير الثيم إلى ملف JSON
        Args:
            theme_id (Optional[int]): معرف الثيم الذي سيتم تصديره. إذا لم يتم تحديده، سيتم تصدير الثيم الافتراضي.
            file_path (str): مسار ملف JSON الذي سيتم حفظ الثيم فيه.
        Returns:
            bool: True إذا تم التصدير بنجاح، False خلاف ذلك.
        """
        try:
            theme_data = self.get_theme_data(theme_id)
            export_data = {
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'theme_id': theme_id or self._current_theme_id,
                    'theme_name': theme_data.get('_metadata', {}).get('theme_name', '')
                },
                'theme': theme_data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Theme exported successfully to {file_path}")
            return True
        except Exception as e:
            print(f"❌ Error exporting theme to JSON: {e}")
            return False
        
    def import_theme_from_json(self, file_path: str, theme_name: str = "imported_theme") -> Optional[int]:
        """استيراد ثيم من ملف JSON
        Args:
            file_path (str): مسار ملف JSON الذي يحتوي على بيانات الثيم.
            theme_name (str): اسم الثيم الجديد الذي سيتم إنشاؤه.
        Returns:
            Optional[int]: معرف الثيم الجديد إذا تم الاستيراد بنجاح، None خلاف ذلك.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            theme_data = import_data.get('theme', {})
            
            # إنشاء ثيم جديد
            query = "INSERT INTO theme (theme_name, state) VALUES (?, 'active') RETURNING theme_id"
            result = self.db_manager.execute_query(query, (theme_name,))
            
            if not result:
                return None
            
            new_theme_id = result[0]['theme_id']
            
            # إدخال البيانات التفصيلية
            self._insert_theme_details(new_theme_id, theme_data)
            
            # مسح الكاش
            self.get_theme_data.cache_clear()
            self._current_theme_cache = None
            
            print(f"✅ Theme imported successfully with ID: {new_theme_id}")
            return new_theme_id
            
        except Exception as e:
            print(f"❌ Error importing theme from JSON: {e}")
            return None
    

    def _insert_theme_details(self, theme_id: int, theme_data: Dict):
        """إدخال البيانات التفصيلية للثيم (دالة مساعدة)"""
        for category, category_data in theme_data.items():
            if isinstance(category_data, dict):
                for subcategory, subcategory_data in category_data.items():
                    if isinstance(subcategory_data, dict):
                        for element_name, element_data in subcategory_data.items():
                            if isinstance(element_data, dict):
                                for property_name, property_value in element_data.items():
                                    if property_name not in ['font_weight', 'font_size']:
                                        query = """
                                        INSERT INTO theme_details 
                                        (theme_id, category, subcategory, element_name, property_name, property_value)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                        """
                                        self.execute_query(
                                            query, 
                                            (theme_id, category, subcategory, element_name, property_name, property_value)
                                        )
    
    def switch_theme(self, theme_id: int) -> bool:
        """تبديل الثيم الحالي
        
        Args:
            theme_id (int): معرف الثيم الذي سيتم التبديل إليه.
        Returns:
            bool: True إذا تم التبديل بنجاح، False خلاف ذلك.
        """
        try:
            # التحقق من وجود الثيم
            query = "SELECT theme_id FROM theme WHERE theme_id = ? AND state = 'active'"
            result = self.execute_query(query, (theme_id,))
            
            if not result:
                print(f"❌ Theme with ID {theme_id} not found or not active")
                return False
            
            # مسح الكاش وتحميل الثيم الجديد
            self.get_theme_data.cache_clear()
            self._current_theme_cache = self.get_theme_data(theme_id)
            self.set_default_theme(theme_id)

            print(f"✅ Switched to theme ID: {theme_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error switching theme: {e}")
            return False

    def _get_default_theme_id(self) -> Optional[int]:
        """الحصول على معرف الثيم الافتراضي"""
        try:
            query = "SELECT theme_id FROM theme WHERE is_default = 1 AND state = 'active' LIMIT 1"
            result = self.execute_query(query)
            return result[0]['theme_id'] if result else None
        except Exception as e:
            print(f"DBM ❌ Error getting default theme ID: {e}")
            return None

        
    def update_theme_element(self, category: str, subcategory: str, element_name: str, 
                            property_name: str, property_value: str, 
                            theme_id: Optional[int] = None,
                            language: Optional[str] = None,
                            font_weight: Optional[str] = None,
                            font_size: Optional[str] = None) -> bool:
        """
        تحديث خاصية معينة في عنصر الثيم
        
        Args:
            category: الفئة (color, typography, button, etc.)
            subcategory: الفئة الفرعية (primary, secondary, etc.)
            element_name: اسم العنصر (blue_trust, primary_button, etc.)
            property_name: اسم الخاصية (hex, background, font_family, etc.)
            property_value: قيمة الخاصية الجديدة
            theme_id: معرف الثيم (اختياري - يستخدم الافتراضي إذا لم يتم تحديد)
            language: اللغة (للفئة typography)
            font_weight: وزن الخط (للفئة typography)
            font_size: حجم الخط (للفئة typography)
        
        Returns:
            bool: True إذا نجح التحديث، False إذا فشل
        """
        try:
            if theme_id is None:
                theme_id = self.get_default_theme()
                if theme_id is None:
                    print("❌ No default theme found")
                    return False
            
            # بناء بيانات التحديث
            update_data = {
                'property_value': property_value
            }
            
            # إضافة بيانات إضافية إذا كانت متوفرة
            if language:
                update_data['language'] = language
            if font_weight:
                update_data['font_weight'] = font_weight
            if font_size:
                update_data['font_size'] = font_size
            
            # بناء جزء SET من الاستعلام
            set_parts = [f"{key} = ?" for key in update_data.keys()]
            values = list(update_data.values())
            
            # بناء شروط WHERE
            where_conditions = [
                "theme_id = ?",
                "category = ?", 
                "subcategory = ?",
                "element_name = ?",
                "property_name = ?"
            ]
            where_values = [theme_id, category, subcategory, element_name, property_name]
            
            # إذا كانت لغة محددة، أضفها للشروط
            if language:
                where_conditions.append("language = ?")
                where_values.append(language)
            else:
                where_conditions.append("language IS NULL")
            
            query = f"""
            UPDATE theme_details 
            SET {', '.join(set_parts)}
            WHERE {' AND '.join(where_conditions)}
            """
            
            # تنفيذ التحديث
            result = self.execute_query(query, tuple(values + where_values), commit=True)
            
            if result is not None:
                # مسح الكاش لإجبار إعادة التحميل
                self.get_theme_data.cache_clear()
                self._current_theme_cache = None
                print(f"✅ Theme element updated successfully: {category}.{subcategory}.{element_name}.{property_name}")
                return True
            else:
                print("❌ Failed to update theme element")
                return False
                
        except Exception as e:
            print(f"❌ Error updating theme element: {e}")
            return False




    def add_theme_details_element(self, data: dict) -> bool:
        """
        إدخال تفاصيل عنصر ثيم جديدة
        
        Args:
            data (dict): { 'category': 'color', 'subcategory': 'status', 'element_name': 'danger_red', 'property_name': 'hex', 'property_value': '#F44336','language':'fr','font_weight':'' , 'font_size':'', 'theme_id': 1 }
        
        Returns:
            bool: True إذا تم الإدخال بنجاح، False خلاف ذلك.
        """

        try:
            default_theme_values = self.get_default_theme()
            keys = ', '.join(data.keys())
            data['theme_id'] = default_theme_values
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())

            query = f"""
                INSERT INTO theme_details ({keys}) VALUES ({placeholders})
            """
            return self.execute_query(query, values, commit=True) is not None
        except Exception as e:
            print(f"DBM ❌ Error inserting theme_details: {e}")
            return False

    def add_complete_theme(self,data:dict,data_theme:dict) -> bool:
        """
        ادخال جميع بيانات الثيم 

        Args:
        data (dict): {'theme_name': 'Dark Theme', 'settings_id': 1, 'state': 'active', 'is_default': 0}

        data_theme (dict) : {
            1:{ 'category': 'color', 'subcategory': 'status', 'element_name': 'danger_red', 'property_name': 'hex', 'property_value': '#F44336','language':'fr','font_weight':'' , 'font_size':'', 'theme_id': 1 },
            2:{ 'category': 'color', 'subcategory': 'primary', 'element_name': '', 'property_name': 'hex', 'property_value': '#2E86AB','language':'fr','font_weight':'' , 'font_size':'', 'theme_id': 1 },
            3:{ 'category': 'color', 'subcategory': 'secondary', 'element_name': '', 'property_name': 'hex', 'property_value': '#4AC336','language':'fr','font_weight':'' , 'font_size':'', 'theme_id': 1 },
            .... etc
        
        }

        Return:            bool: True إذا تم الإدخال بنجاح، False خلاف ذلك.

        """
        
        self.add_theme(data)
        try:
            if not data_theme:
                return False
            for key, value in data_theme.items():
                data_element = value
                data_element['theme_id'] = self.get_last_theme()
                self.add_theme_details_element(data_element)


        except Exception as e:
            print(f"DBM ❌ Error inserting the complet theme {e}")
            return False

    

    
# ----------------------------------------------------------------------
# 2. دوال المستخدمين والعملاء (Users & Clients)
# ----------------------------------------------------------------------

    def add_user(self, data: Dict) -> Optional[int]:
        """إضافة مستخدم جديد
        Args: 
            data (Dict):{'username': 'user1', 'password_hash': 'hashed_pw', 'full_name': 'User One', 'role': 'receptionist', 'created_at': '2024-06-01T12:00:00'}
              قاموس يحتوي على الحقول التي سيتم إدخالها، e.g
        Returns:
            Optional[int]: معرف المستخدم الجديد إذا تم الإدخال بنجاح، None خلاف ذلك.
        """

        try:
            """إضافة موظف استقبال جديد"""
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT INTO Users ({keys}) VALUES ({placeholders})"
            return self.execute_query(query, values, commit=True)
        except Exception as e:
            print(f"DBM ❌ Error adding user: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """استرداد مستخدم بناءً على اسم المستخدم (لتسجيل الدخول)
        Args:
            username (str): اسم المستخدم الذي سيتم البحث عنه.
        Returns:
            Optional[Dict]: {'user_id': 1, 'username': 'user1', 'password_hash': 'hashed_pw', 'full_name': 'User One', 'role': 'receptionist', 'created_at': '2024-06-01T12:00:00'}
                قاموس يحتوي على حقول المستخدم، أو None إذا لم يتم العثور على المستخدم.
        """
        try:
            query = "SELECT * FROM Users WHERE username = ?"
            result = self.execute_query(query, (username,), fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getting user by username: {e}")
            return None
    
    def add_client(self, data: Dict) -> Optional[int]:
        """إضافة عميل جديد
        Args:
            data (Dict): {'full_name': 'Client One', 'phone_number': '123456789', 'email': 'client@example.com', 'notes': 'VIP client', 'created_at': '2024-06-01T12:00:00'}
        Returns:
            Optional[int]: معرف العميل الجديد إذا تم الإدخال بنجاح، None خلاف ذلك.
        """
        try:
            data['created_at'] = datetime.now().isoformat()
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT INTO Clients ({keys}) VALUES ({placeholders})"
            return self.execute_query(query, values, commit=True)
        except Exception as e:
            print(f"DBM ❌ Error adding client: {e}")
            return None
        
    def get_client_details(self, client_id: int) -> Optional[Dict]:
        """استرداد تفاصيل عميل واحد
        Args:
            client_id (int): معرف العميل الذي سيتم استرداد تفاصيله.

        Returns:
            Optional[Dict]: {'client_id': 1, 'full_name': 'Client One', 'phone_number': '123456789', 'email': 'client@example.com', 'notes': 'VIP client', 'created_at': '2024-06-01T12:00:00'}
                قاموس يحتوي على حقول العميل، أو None إذا لم يتم العثور على العميل.
        """
        try:
            query = "SELECT * FROM Clients WHERE client_id = ?"
            result = self.execute_query(query, (client_id,), fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getting client details: {e}")
            return None
    
    def search_clients(self, search_term: str) -> List[Dict]:
        """البحث عن عملاء بالاسم أو الهاتف (للإدخال و التقارير)
        Args:
            search_term (str): مصطلح البحث للبحث في حقول full_name أو phone_number.
        Returns:
            List[Dict]: [{'client_id': 1, 'full_name': 'Client One', 'phone_number': '123456789', 'email': 'client@example.com', 'notes': 'VIP client', 'created_at': '2024-06-01T12:00:00'}]"""
      
        try:
            term = f'%{search_term}%'
            query = "SELECT client_id, full_name, phone_number, email FROM Clients WHERE full_name LIKE ? OR phone_number LIKE ?"
            results = self.execute_query(query, (term, term))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error searching clients: {e}")
            return []

    def get_client_appointments_history(self, client_id: int) -> List[Dict]:
        """استرداد جميع مواعيد عميل محدد (لتتبع العميل)
        Args:
            client_id (int): معرف العميل الذي سيتم استرداد تاريخ مواعيده.
        Returns:
            List[Dict]: [{'appointment_id': 1, 'client_id': 1, 'user_id': 1, 'service_id': 2, 'date': '2024-06-10', 'start_time': '10:00', 'duration_minutes': 30, 'status': 'confirmed', 'notes': '', 'is_paid': 0, 'reminder_set': 0, 'created_at': '2024-06-01T12:00:00', 'updated_at': '2024-06-01T12:00:00', 'service_name': 'Service One'}]
        """

        try:
            query = """
            SELECT A.*, S.name_ar as service_name
            FROM Appointments A
            LEFT JOIN Services S ON A.service_id = S.service_id
            WHERE A.client_id = ?
            ORDER BY A.date DESC, A.start_time DESC
            """
            results = self.execute_query(query, (client_id,))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error getting client appointments history: {e}")
            return []

# ----------------------------------------------------------------------
# 3. دوال المواعيد والخدمات (Appointments & Services)
# ----------------------------------------------------------------------
    def add_service(self, data: Dict) -> Optional[int]:
        """إضافة خدمة جديدة
        Args:
            data (Dict): {'name_ar': 'Service One', 'name_fr': 'Service Un', 'price': 50.0, 'duration_minutes': 30, 'is_active': 1}
        Returns:
            Optional[int]: معرف الخدمة الجديدة إذا تم الإدخال بنجاح، None خلاف ذلك.
        """
         

        try:
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT INTO Services ({keys}) VALUES ({placeholders})"
            return self.execute_query(query, values, commit=True)
        except Exception as e:
            print(f"DBM ❌ Error adding service: {e}")
            return None
    
    def add_appointment(self, data: Dict) -> Optional[int]:
        """إضافة موعد جديد
        Args:
            data (Dict):{'client_id': 1, 'user_id': 1, 'service_id': 2, 'date': '2024-06-10', 'start_time': '10:00', 'duration_minutes': 30, 'status': 'confirmed', 'notes': '', 'is_paid': 0, 'reminder_set': 0, 'created_at': '2024-06-01T12:00:00', 'updated_at': '2024-06-01T12:00:00'}
        Returns:
            Optional[int]: معرف الموعد الجديد إذا تم الإدخال بنجاح، None خلاف ذلك.
        """
        try:
            """إضافة موعد جديد"""
            now = datetime.now().isoformat()
            data['created_at'] = now
            data['updated_at'] = now
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT INTO Appointments ({keys}) VALUES ({placeholders})"
            return self.execute_query(query, values, commit=True)
        except Exception as e:
            print(f"DBM ❌ Error adding appointment: {e}")
            return None

    def update_appointment(self, appointment_id: int, data: Dict) -> bool:
        """تحديث موعد موجود
        
        Args:
            appointment_id (int): معرف الموعد الذي سيتم تحديثه.
            data (Dict): قاموس يحتوي على الحقول التي سيتم تحديثها، e.g {'status': 'canceled', 'notes': 'Client called to cancel'}{'client_id': 1, 'user_id': 1, 'service_id': 2, 'date': '2024-06-10', 'start_time': '10:00', 'duration_minutes': 30, 'status': 'confirmed', 'notes': '', 'is_paid': 0, 'reminder_set': 0, 'created_at': '2024-06-01T12:00:00', 'updated_at': '2024-06-01T12:00:00'}
        Returns:
            bool: True إذا تم التحديث بنجاح، False خلاف ذلك.       
        """
        try:
            
            """تحديث موعد موجود (تغيير الحالة، الوقت، إلخ)"""
            data['updated_at'] = datetime.now().isoformat()
            set_parts = [f"{k} = ?" for k in data.keys()]
            values = list(data.values())
            values.append(appointment_id)
        
            query = f"UPDATE Appointments SET {', '.join(set_parts)} WHERE appointment_id = ?"
            return self.execute_query(query, tuple(values), commit=True) is not None
        except Exception as e:
            print(f"DBM ❌ Error updating appointment: {e}")
            return False
        
    def get_daily_appointments(self, date: str) -> List[Dict]:
        """استرداد جميع المواعيد ليوم محدد (للرؤية اليومية)
        Args:
            date (str):  'YYYY-MM-DD' format التاريخ الذي سيتم استرداد المواعيد له.
        Returns:
            the result will be a list of dictionaries containing the appointment fields along with client_name, phone_number , service_name_ar, service_name_fr, ORDER start_time  e.g.,
            List[Dict]:[{'appointment_id': 1,'client_id': 1, 'user_id': 1, 'service_id': 2, 'date': '2024-06-10', 'start_time': '10:00', 'duration_minutes': 30, 'status': 'confirmed', 'notes': '', 'is_paid': 0, 'reminder_set': 0, 'created_at': '2024-06-01T12:00:00', 'updated_at': '2024-06-01T12:00:00', 'client_name': 'Client One', 'phone_number': '123456789', 'service_name_ar': 'Service One', 'service_name_fr': 'Service Un'}]
        """
        try:    
            query = """
            SELECT 
                A.*, 
                C.full_name as client_name, 
                C.phone_number,
                S.name_ar as service_name_ar,
                S.name_fr as service_name_fr
            FROM Appointments A
            JOIN Clients C ON A.client_id = C.client_id
            LEFT JOIN Services S ON A.service_id = S.service_id
            WHERE A.date = ?
            ORDER BY A.start_time
            """
            results = self.execute_query(query, (date,))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error getting daily appointments: {e}")
            return []
        
    def get_weekly_appointments(self, start_date: str, end_date: str) -> List[Dict]:
        """استرداد جميع المواعيد لمدى زمني محدد (للرؤية الأسبوعية/الشهرية)
        Args:
            start_date (str): 'YYYY-MM-DD' format بداية المدى الزمني.
            end_date (str): 'YYYY-MM-DD' format نهاية المدى الزمني.
        Returns:the result will be a list of dictionaries containing the appointment fields along with client_name, service_name_ar, service_name_fr, date BETWEEN start_date, end_date ORDER BY appointments date, appointments start_time e.g.,
            List[Dict]:[{'date': '2024-06-10', 'start_time': '10:00', 'duration_minutes': 30, 'status': 'confirmed', 'client_name': 'Client One', 'service_name_ar': 'Service One', 'service_name_fr': 'Service Un'}]
        """
  
        try:
            """استرداد جميع المواعيد لمدى زمني محدد (للرؤية الأسبوعية/الشهرية)"""
            query = """
            SELECT 
                A.date, A.start_time, A.duration_minutes, A.status,
                C.full_name as client_name, 
                S.name_ar as service_name_ar,
                S.name_fr as service_name_fr
            FROM Appointments A
            JOIN Clients C ON A.client_id = C.client_id
            LEFT JOIN Services S ON A.service_id = S.service_id
            WHERE A.date BETWEEN ? AND ?
            ORDER BY A.date, A.start_time
            """
            results = self.execute_query(query, (start_date, end_date))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error getting weekly appointments: {e}")
            return []
        
    def get_all_services(self) -> List[Dict]:
        """استرداد جميع الخدمات المتاحة
        Args:
            None
        Returns:the result will be a list of dictionaries containing the service fields, e.g.,
            List[Dict]: [{'service_id': 1, 'name_ar': 'خدمة واحدة', 'name_fr': 'Service One', 'price': 100, 'duration_minutes': 30, 'is_active': 1}]
        """

        try:
            query = "SELECT * FROM Services WHERE is_active = 1"
            results = self.execute_query(query)
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error getting all services: {e}")
            return []


# ----------------------------------------------------------------------
# 4. دوال التقارير والإحصائيات (Reports & Analytics)
# ----------------------------------------------------------------------

    def get_attendance_stats(self, start_date: str, end_date: str) -> List[Dict]:
        """استرداد إحصائيات الحضور/الغياب/الإلغاء لفترة زمنية محددة
        Args:
            start_date (str): 'YYYY-MM-DD' format بداية المدى الزمني.
            end_date (str): 'YYYY-MM-DD' format نهاية المدى الزمني.
        Returns:
            List[Dict]: [{'status': 'confirmed', 'count': 10}, {'status': 'canceled', 'count': 5}]
        """
        try:
            """تقارير الإحصاءات الذكية: نسبة الحضور/الغياب/الإلغاء"""
            query = """
            SELECT 
                status, 
                COUNT(appointment_id) as count
            FROM Appointments
            WHERE date BETWEEN ? AND ?
            GROUP BY status
            """
            results = self.execute_query(query, (start_date, end_date))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error getting attendance stats: {e}")
            return []
        
    def get_peak_hours_stats(self, start_date: str, end_date: str) -> List[Dict]:
        """إحصائية ساعات الذروة (بناءً على بداية الساعة)
        Args:
            start_date (str): 'YYYY-MM-DD' format بداية المدى الزمني.
            end_date (str): 'YYYY-MM-DD' format نهاية المدى الزمني.
        Returns:
            List[Dict]: [{'hour': '10', 'count': 15}, {'hour': '11', 'count': 10}]
        """
 
        query = """
        SELECT 
            STRFTIME('%H', start_time) as hour, 
            COUNT(appointment_id) as count
        FROM Appointments
        WHERE date BETWEEN ? AND ? AND status IN ('Confirmed', 'Attended')
        GROUP BY hour
        ORDER BY count DESC
        """
        
        try:
            results = self.execute_query(query, (start_date, end_date))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error getting peak hours stats: {e}")
            return []

# ----------------------------------------------------------------------
# 5. دوال الترجمة والفواتير (Translations & Invoices)
# ----------------------------------------------------------------------

    def get_translations(self) -> Dict[str, Dict[str, str]]:
        """استرداد جميع الترجمات لمدير الترجمة (Translation Manager)
        Args:
            None
        Returns:the result will be a dictionary in the format
            Dict[str, Dict[str, str]]:  {'key': {'ar': 'النص', 'fr': 'Texte', 'en': 'Text'}}
        """
        try:
            query = "SELECT key, ar, fr, en FROM Translations"
            results = self.execute_query(query)

            # تحويل النتائج إلى قاموس: {'key': {'ar': 'النص', 'fr': 'Texte'}}
            translation_dict = {}
            for row in results:
                translation_dict[row['key']] = {'ar': row['ar'], 'fr': row['fr'], 'en': row['en']}
            return translation_dict
        except Exception as e:
            print(f"DBM ❌ Error getting translations: {e}")
            return {}

    def insert_translation(self, key: str, ar_text: str, fr_text: str, en_text: str) -> Optional[int]:
        """إدخال ترجمة جديدة
        Args:
            key (str): المفتاح الفريد للنص المترجم.
            ar_text (str): الترجمة العربية.
            fr_text (str): الترجمة الفرنسية.
            en_text (str): الترجمة الإنجليزية.
        Returns:
            Optional[int]: معرف السجل الجديد إذا تم الإدخال بنجاح، None خلاف ذلك
        """
        try:
            query = "INSERT INTO Translations (key, ar, fr, en) VALUES (?, ?, ?, ?)"
            return self.execute_query(query, (key, ar_text, fr_text, en_text), commit=True)
        except Exception as e:
            print(f"DBM ❌ Error inserting translation: {e}")
            return None

    def add_invoice(self, data: Dict) -> Optional[int]:
        """إضافة فاتورة جديدة
        Args:
            data (Dict):{ 'appointment_id': 1, 'created_by_user_id': 1,'issue_date': '2023-01-01', 'total_amount': 150.0, 'payment_status': 'unpaid'}
        Returns:
            Optional[int]: معرف الفاتورة الجديدة إذا تم الإدخال بنجاح، None خلاف
        """    

        try:
            """إنشاء فاتورة جديدة"""
            data['issue_date'] = datetime.now().isoformat()
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT INTO Invoices ({keys}) VALUES ({placeholders})"
            return self.execute_query(query, values, commit=True)
        except Exception as e:
            print(f"DBM ❌ Error adding invoice: {e}")
            return None
        
    def get_invoice_by_appointment(self, appointment_id: int) -> Optional[Dict]:
        """استرداد فاتورة بناءً على مُعرِّف الموعد (لطباعة الفاتورة)
        Args:
            appointment_id (int): مُعرِّف الموعد.
        Returns:
            Optional[Dict]: {'invoice_id': 1, 'invoice_number': 1001, 'appointment_id': 1, 'created_by_user_id': 1,'issue_date': '2023-01-01', 'total_amount': 150.0, 'payment_status': 'unpaid', 'client_name': 'Client One', 'date': '2024-06-10', 'start_time': '10:00'}
        """
        query = """
        SELECT 
            I.*, 
            C.full_name as client_name, 
            A.date, 
            A.start_time
        FROM Invoices I
        JOIN Appointments A ON I.appointment_id = A.appointment_id
        JOIN Clients C ON A.client_id = C.client_id
        WHERE I.appointment_id = ?
        """
        try:
            result = self.execute_query(query, (appointment_id,), fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getting invoice by appointment: {e}")
            return None
# ----------------------------------------------------------------------
# 6. دوال  (Audit_Logs & )
# ----------------------------------------------------------------------
    def create_audit_log(self, data: Dict) -> Optional[int]:

        """إضافة سجل تدقيق جديد
        Args:
            data (Dict): قاموس يحتوي على الحقول التي سيتم إدخالها، e.g., {'user_id': 1, 'timestamp': '2024-06-01T12:00:00', 'action_type': 'create_appointment', 'details': 'Created appointment for client_id 1', 'related_data': ''}
        Returns:
            Optional[int]: معرف سجل التدقيق الجديد إذا تم الإدخال بنجاح، None خلاف
        """


        try:
            data['timestamp'] = datetime.now().isoformat()
            key = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT INTO Audit_Logs ({key}) VALUES ({placeholders})"
            return self.execute_query(query, values, commit=True)
        except Exception as e:
            print(f"DBM ❌ Error creating audit log: {e}")
            return None


    