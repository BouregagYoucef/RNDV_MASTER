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
	"user_id" INTEGER PRIMARY KEY,
	"username" VARCHAR NOT NULL UNIQUE,
	"password_hash" VARCHAR NOT NULL,
	"full_name" VARCHAR,
	"is_active" BOOLEAN DEFAULT 1 -- SQLite uses 1 for True, 0 for False
);""",

""" 

CREATE TABLE IF NOT EXISTS "Clients" (
	"client_id" INTEGER PRIMARY KEY,
	"full_name" VARCHAR NOT NULL,
	"phone_number" VARCHAR UNIQUE,
	"email" VARCHAR,
	"notes" TEXT,
	"created_at" TEXT -- TEXT for TIMESTAMP (ISO8601)
);""",

""" 

CREATE TABLE IF NOT EXISTS "Services" (
	"service_id" INTEGER PRIMARY KEY,
	"name_ar" VARCHAR NOT NULL,
	"name_fr" VARCHAR,
	"price" REAL DEFAULT 0.0,
	"duration_minutes" INTEGER,
	"is_active" BOOLEAN DEFAULT 1
);""",

""" 

CREATE TABLE IF NOT EXISTS "Appointments" (
	"appointment_id" INTEGER PRIMARY KEY,
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
	"translation_id" INTEGER PRIMARY KEY,
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
	"log_id" INTEGER PRIMARY KEY,
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
	"invoice_id" INTEGER PRIMARY KEY,
	"invoice_number" INTEGER NOT NULL UNIQUE,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,        -- الفئة (color, typography, button, etc.)
    subcategory TEXT,              -- الفئة الفرعية (primary, secondary, etc.)
    element_name TEXT NOT NULL,    -- اسم العنصر
    property_name TEXT NOT NULL,   -- اسم الخاصية
    property_value TEXT NOT NULL,  -- قيمة الخاصية
    language TEXT,                 -- اللغة (ar, en) للطباعة
    font_weight TEXT,              -- وزن الخط (للطباعة)
    font_size TEXT,                -- حجم الخط (للطباعة)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    "settings_id" INTEGER UNIQUE,
    FOREIGN KEY ("settings_id") REFERENCES "Settings"("id")
    ON UPDATE NO ACTION ON DELETE NO ACTION
);
"""
]
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

# إدخال بيانات الألوان
default_theme_values = {""""
INSERT INTO theme (category, subcategory, element_name, property_name, property_value) VALUES
-- إدخال بيانات الألوان
('color', 'primary', 'blue_trust', 'hex', '#2E86AB'),
('color', 'primary', 'pure_white', 'hex', '#FFFFFF'),
('color', 'primary', 'charcoal_black', 'hex', '#2A2D34'),
('color', 'secondary', 'light_blue', 'hex', '#6BBAD6'),
('color', 'secondary', 'light_gray', 'hex', '#F8F9FA'),
('color', 'secondary', 'medium_gray', 'hex', '#E9ECEF'),
('color', 'status', 'success_green', 'hex', '#4CAF50'),
('color', 'status', 'warning_orange', 'hex', '#FF9800'),
('color', 'status', 'danger_red', 'hex', '#F44336');
""","""
-- إدخال بيانات الطباعة العربية
INSERT INTO theme (category, subcategory, element_name, property_name, property_value, language, font_weight, font_size) VALUES
('typography', 'main_title', 'arabic_main_title', 'font_family', 'IBM Plex Sans Arabic', 'ar', 'Bold', '24px'),
('typography', 'subtitle', 'arabic_subtitle', 'font_family', 'IBM Plex Sans Arabic', 'ar', 'SemiBold', '18px'),
('typography', 'normal_text', 'arabic_normal', 'font_family', 'IBM Plex Sans Arabic', 'ar', 'Regular', '16px'),
('typography', 'secondary_text', 'arabic_secondary', 'font_family', 'IBM Plex Sans Arabic', 'ar', 'Light', '14px');
""","""
-- إدخال بيانات الطباعة الإنجليزية
INSERT INTO theme (category, subcategory, element_name, property_name, property_value, language, font_weight, font_size) VALUES
('typography', 'main_title', 'english_main_title', 'font_family', 'Inter', 'en', 'Bold', '24px'),
('typography', 'subtitle', 'english_subtitle', 'font_family', 'Inter', 'en', 'SemiBold', '18px'),
('typography', 'normal_text', 'english_normal', 'font_family', 'Inter', 'en', 'Regular', '16px'),
('typography', 'secondary_text', 'english_secondary', 'font_family', 'Inter', 'en', 'Light', '14px');
""","""
-- إدخال بيانات الأزرار
INSERT INTO theme (category, subcategory, element_name, property_name, property_value) VALUES
('button', 'primary', 'primary_button', 'background', '#2E86AB'),
('button', 'primary', 'primary_button', 'text_color', '#FFFFFF'),
('button', 'primary', 'primary_button', 'border_radius', '8px'),
('button', 'primary', 'primary_button', 'box_shadow', '0px 2px 4px rgba(46, 134, 171, 0.2)'),
('button', 'secondary', 'secondary_button', 'background', 'transparent'),
('button', 'secondary', 'secondary_button', 'border', '1px solid #2E86AB'),
('button', 'secondary', 'secondary_button', 'text_color', '#2E86AB'),
('button', 'secondary', 'secondary_button', 'border_radius', '8px'),
('button', 'hover', 'button_hover', 'box_shadow', '0px 4px 8px rgba(46, 134, 171, 0.3)'),
('button', 'hover', 'button_hover', 'transform', 'translateY(-1px)');
""","""
-- إدخال بيانات الحقول والنماذج
INSERT INTO theme (category, subcategory, element_name, property_name, property_value) VALUES
('form', 'input', 'input_field', 'background', '#FFFFFF'),
('form', 'input', 'input_field', 'border', '1px solid #E9ECEF'),
('form', 'input', 'input_field', 'border_radius', '6px'),
('form', 'input', 'input_field', 'box_shadow', '0px 0px 0px 2px rgba(46, 134, 171, 0.1)'),
('form', 'focus', 'input_focus', 'border', '1px solid #2E86AB'),
('form', 'focus', 'input_focus', 'box_shadow', '0px 0px 0px 3px rgba(46, 134, 171, 0.15)');
""","""
-- إدخال بيانات الأيقونات
INSERT INTO theme (category, subcategory, element_name, property_name, property_value) VALUES
('icon', 'style', 'line_icons', 'type', 'Line Icons'),
('icon', 'style', 'line_icons', 'stroke_width', '1.5px'),
('icon', 'size', 'main_icons', 'size', '20px'),
('icon', 'size', 'secondary_icons', 'size', '16px'),
('icon', 'color', 'icon_default', 'color', '#2A2D34'),
('icon', 'color', 'icon_active', 'color', '#6BBAD6');
""","""
-- إدخال بيانات التقويم
INSERT INTO theme (category, subcategory, element_name, property_name, property_value) VALUES
('calendar', 'current_day', 'current_day', 'background', '#2E86AB'),
('calendar', 'current_day', 'current_day', 'text_color', '#FFFFFF'),
('calendar', 'selected_day', 'selected_day', 'background', '#6BBAD6'),
('calendar', 'selected_day', 'selected_day', 'text_color', '#FFFFFF'),
('calendar', 'normal_day', 'normal_day', 'background', '#FFFFFF'),
('calendar', 'normal_day', 'normal_day', 'text_color', '#2A2D34'),
('calendar', 'appointment', 'confirmed', 'border_color', '#4CAF50'),
('calendar', 'appointment', 'pending', 'border_color', '#FF9800'),
('calendar', 'appointment', 'cancelled', 'border_color', '#E9ECEF'),
('calendar', 'appointment', 'cancelled', 'text_decoration', 'line-through');
""","""
-- إدخال بيانات الرسوم المتحركة
INSERT INTO theme (category, subcategory, element_name, property_name, property_value) VALUES
('animation', 'timing', 'default', 'duration', '0.3s'),
('animation', 'timing', 'default', 'timing_function', 'ease-out'),
('animation', 'types', 'animations', 'list', 'fade-in, slide-up, scale');
""","""
-- إدخال بيانات التباعد
INSERT INTO theme (category, subcategory, element_name, property_name, property_value) VALUES
('spacing', 'scale', 'base_unit', 'size', '8px'),
('spacing', 'sizes', 'small', 'size', '8px'),
('spacing', 'sizes', 'medium', 'size', '16px'),
('spacing', 'sizes', 'large', 'size', '24px'),
('spacing', 'sizes', 'xlarge', 'size', '32px');
"""}

class DatabaseManager:
    """
    مدير قاعدة البيانات: مسؤول عن الاتصال بقاعدة البيانات وتنفيذ جميع عمليات CRUD والتقارير.
    """

    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        self._conn = None
        self._cursor = None
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
        print(f"\n\n = ========DBM ⚙️ Executing query in table: {query[12:50]}  ")
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
            print("DBM ⚙️ Inserting default translation keys...")
            self.execute_query(translations_keys, commit=True)
            for i in default_theme_values:
                self.execute_query(i, commit=True)
            print("DBM ✅  Default translation keys and theme values ensured.")
        except Exception as e:
            print(f"DBM ❌ Error inserting default translation keys or theme values: {e}")




# ----------------------------------------------------------------------
# 1. دوال الإعدادات والتراخيص (Settings & Licensing)
# ----------------------------------------------------------------------

    def set_default_settings(self):
        try:
            """إنشاء سجل إعدادات افتراضي إذا كان الجدول فارغًا"""
            query = "INSERT INTO Settings (id, company_name, language,hardware_id) VALUES (1, 'Appointment Manager', 'ar', 'dummy_hardware_id')"
            self.execute_query(query, commit=True)
            print("DBM ✅  Default settings ensured.")
        except Exception as e:
            print(f"DBM ❌ Error setting default settings: {e}")

    def get_settings(self) -> Optional[Dict]:
        """استرداد جميع الإعدادات"""
        try:
            query = "SELECT * FROM Settings"
            result = self.execute_query(query, fetch_one=True)
            print(f"DBM ⚙️ Retrieved settings: {result}")
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getter settings retrieving settings: {e}")
            return None
    
    def update_settings(self, data: Dict) -> bool:
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
        try:
            """استرداد معلومات الجهاز (Getter)"""
            query = "SELECT * FROM Device_Info WHERE id = 1"
            result = self.execute_query(query, fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getter device info retrieving device info: {e}")
            return None
        
    def set_license_info(self, data: Dict) -> bool:
        try:
            """إدخال/تحديث معلومات الترخيص"""
            keys = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            values = tuple(data.values())
            query = f"INSERT OR REPLACE INTO Licenses (id, {keys}) VALUES (1, {placeholders})"
            return self.execute_query(query, values, commit=True) is not None
        except Exception as e:
            print(f"DBM ❌ Error setter license setting license info: {e}")
            return False
    
    def get_license_info(self) -> Optional[Dict]:
        """استرداد معلومات الترخيص"""
        try:
            query = "SELECT * FROM Licenses WHERE id = 1"
            result = self.execute_query(query, fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getter license retrieving license info: {e}")
            return None
# أضف هذه الدوال في القسم الخاص بـ "دوال الإعدادات والتراخيص" في DatabaseManager

    def set_default_theme(self):
        pass  # يمكن تنفيذها إذا لزم الأمر
    
    def set_default_license_info(self):
        try:
            """إنشاء سجل ترخيص افتراضي إذا كان الجدول فارغًا"""
            query = "INSERT OR IGNORE INTO Licenses (id, is_active) VALUES (1, 0)"
            self.execute_query(query, commit=True)
        except Exception as e:
            print(f"DBM ❌ Error setting default license info: {e}")
            return False

    def get_theme_settings(self) -> Optional[Dict]:
        """استرداد جميع إعدادات التنسيق (Getter)"""
        try:
            query = "SELECT * FROM theme"
            result = self.execute_query(query)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getter theme retrieving theme settings: {e}")
            return None
    
    def get_theme_by_category(self, category: str) -> List[Dict]:
        """استرداد إعدادات التنسيق بناءً على الفئة (مثل color, typography, button)"""
        try:
            query = "SELECT * FROM theme WHERE category = ?"
            results = self.execute_query(query, (category,))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error getting theme by category: {e}")
            return []
        
        
    def get_theme_by_element(self, element_name: str) -> List[Dict]:
        """استرداد إعدادات التنسيق بناءً على اسم العنصر (مثل primary_button, arabic_main_title)"""
        try:
            query = "SELECT * FROM theme WHERE element_name = ?"
            results = self.execute_query(query, (element_name,))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error getting theme by element: {e}")
            return []
        

    def update_theme_settings(self, data: Dict) -> bool:
        try:
            """تحديث إعدادات التنسيق (Setter)"""
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
# ----------------------------------------------------------------------
# 2. دوال المستخدمين والعملاء (Users & Clients)
# ----------------------------------------------------------------------

    def add_user(self, data: Dict) -> Optional[int]:
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
        """استرداد مستخدم بناءً على اسم المستخدم (لتسجيل الدخول)"""
        try:
            query = "SELECT * FROM Users WHERE username = ?"
            result = self.execute_query(query, (username,), fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getting user by username: {e}")
            return None
    
    def add_client(self, data: Dict) -> Optional[int]:
        try:
            """إضافة عميل جديد"""
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
        """استرداد تفاصيل عميل واحد"""
        try:
            query = "SELECT * FROM Clients WHERE client_id = ?"
            result = self.execute_query(query, (client_id,), fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getting client details: {e}")
            return None
    
    def search_clients(self, search_term: str) -> List[Dict]:
        try:
            """البحث عن عملاء بالاسم أو الهاتف (للإدخال و التقارير)"""
            term = f'%{search_term}%'
            query = "SELECT client_id, full_name, phone_number, email FROM Clients WHERE full_name LIKE ? OR phone_number LIKE ?"
            results = self.execute_query(query, (term, term))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"DBM ❌ Error searching clients: {e}")
            return []

    def get_client_appointments_history(self, client_id: int) -> List[Dict]:
        try:
            """استرداد جميع مواعيد عميل محدد (لتتبع العميل)"""
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

    def add_appointment(self, data: Dict) -> Optional[int]:
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
        try:    
            """استرداد جميع المواعيد ليوم محدد (للرؤية اليومية)"""
            query = """
            SELECT 
                A.*, 
                C.full_name as client_name, 
                C.phone_number,
                S.name_ar as service_name
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
        try:
            """استرداد جميع المواعيد لمدى زمني محدد (للرؤية الأسبوعية/الشهرية)"""
            query = """
            SELECT 
                A.date, A.start_time, A.duration_minutes, A.status,
                C.full_name as client_name, 
                S.name_ar as service_name
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
        try:
            """استرداد قائمة بجميع الخدمات المتاحة"""
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
        """إحصائية ساعات الذروة (بناءً على بداية الساعة)"""
        query = """
        SELECT 
            STRFTIME('%H', start_time) as hour, 
            COUNT(appointment_id) as count
        FROM Appointments
        WHERE date BETWEEN ? AND ? AND status IN ('Confirmed', 'Attended')
        GROUP BY hour
        ORDER BY count DESC
        """
        results = self.execute_query(query, (start_date, end_date))
        return [dict(row) for row in results] if results else []

    def get_peak_hours_stats(self, start_date: str, end_date: str) -> List[Dict]:
        """إحصائية ساعات الذروة (بناءً على بداية الساعة)"""
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
        try:
            """استرداد جميع الترجمات لمدير الترجمة (Translation Manager)"""
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
        try:
            """إدخال ترجمة جديدة"""
            query = "INSERT INTO Translations (key, ar, fr, en) VALUES (?, ?, ?, ?)"
            return self.execute_query(query, (key, ar_text, fr_text, en_text), commit=True)
        except Exception as e:
            print(f"DBM ❌ Error inserting translation: {e}")
            return None

    def add_invoice(self, data: Dict) -> Optional[int]:
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
        """استرداد فاتورة بناءً على مُعرِّف الموعد (لطباعة الفاتورة)"""
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



    