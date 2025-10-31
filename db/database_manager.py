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
	"fr" TEXT
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
	"id" INTEGER PRIMARY KEY, 
	"Primary_color" VARCHAR,
	"Primary_Light" VARCHAR,
	"Primary_Dark" VARCHAR,
	"Secondary_color" VARCHAR,
	"Secondary_Light" VARCHAR,
	"Secondary_Dark" VARCHAR,
	"Neutral_Dark" VARCHAR,
	"Neutral_Medium" VARCHAR,
	"Neutral_Light" VARCHAR,
	"Background" VARCHAR,
	"Surface_Cards" VARCHAR,
	"Error" VARCHAR,
	"Warning" VARCHAR,
	"Success" VARCHAR,
	"Primary_font" VARCHAR,
	"Headings_font" VARCHAR,
    "settings_id" INTEGER UNIQUE,
    FOREIGN KEY ("settings_id") REFERENCES "Settings"("id")
    ON UPDATE NO ACTION ON DELETE NO ACTION
);
"""
]


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
    # def initialize_db(self):
    #     """إنشاء الجداول إذا لم تكن موجودة"""
    #     try:
    #         self.execute_query(SCHEMA_SQL)
    #         # التأكد من وجود سجل واحد للإعدادات والتراخيص (إذا لم يكن موجوداً)
    #         self.set_default_settings()
    #         self.set_default_license_info()
    #     except Exception as e:
    #         print(f"Error initializing database: {e}")


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
        try:    # قيم افتراضية للتنسيق (يمكنك تعديلها لاحقاً)
            """إنشاء سجل تنسيق افتراضي إذا كان الجدول فارغاً"""
            default_colors = {
                'id': 1,
                'Primary_color': '#007ACC',
                'Primary_Light': '#4CAAEB', 
                'Primary_Dark': '#005F9A',
                'Secondary_color': '#00B689',
                'Secondary_Light': '#33D3A9',
                'Secondary_Dark': '#009C6C',
                'Neutral_Dark': '#1E1E1E',
                'Neutral_Medium': '#6E6E6E',
                'Neutral_Light': '#EDEDED',
                'Background': '#F3F4F6',
                'Surface_Cards': '#FFFFFF',
                'Error': '#E53935',
                'Warning': '#FFB300', 
                'Success': '#43A047',
                'Primary_font': 'Arial',
                'Headings_font': 'Segoe UI',
                'settings_id': 1
            }
        
        
            # إنشاء استعلام INSERT OR IGNORE لضمان عدم تكرار الإدخال
            keys = ', '.join(default_colors.keys())
            placeholders = ', '.join(['?'] * len(default_colors))
            values = tuple(default_colors.values())

            query = f"INSERT  OR REPLACE  INTO theme ({keys}) VALUES ({placeholders})"
            self.execute_query(query, values, commit=True)
        except Exception as e:
            print(f"DBM ❌ Error setting default theme: {e}")
            return False
    
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
            query = "SELECT * FROM theme WHERE id = 1"
            result = self.execute_query(query, fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            print(f"DBM ❌ Error getter theme retrieving theme settings: {e}")
            return None
    
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
            query = "SELECT key, ar, fr FROM Translations"
            results = self.execute_query(query)

            # تحويل النتائج إلى قاموس: {'key': {'ar': 'النص', 'fr': 'Texte'}}
            translation_dict = {}
            for row in results:
                translation_dict[row['key']] = {'ar': row['ar'], 'fr': row['fr']}
            return translation_dict
        except Exception as e:
            print(f"DBM ❌ Error getting translations: {e}")
            return {}
    
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
