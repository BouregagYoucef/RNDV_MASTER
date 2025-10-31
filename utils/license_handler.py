import json
import os
from datetime import datetime, date
import sys
from typing import Dict, Optional, Any

# مكتبات التشفير
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# استيراد مدير قاعدة البيانات
# يجب تعديل مسار الاستيراد بناءً على مكان ملف database_manager.py
# إضافة المسار الأساسي للنظام
# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# sys.path.insert(0, parent_dir)
# try:
#     # استيراد مدير قاعدة البيانات
#     from db.database_manager import DatabaseManager
# except ImportError as e:
#     print(f"❌ خطأ في استيراد DatabaseManager: {e}")
#     DatabaseManager = None
from db.database_manager import DatabaseManager  # تأكد من المسار الصحيح

# استيراد الدوال المساعدة لتوليد بصمة الجهاز
from utils.machine_fingerprint import generate_machine_id_hash 
a = generate_machine_id_hash()
print("🔧 Imported generate_machine_id_hash from utils.machine_fingerprint is \n", a)
# مسارات الملفات (يجب تعريفها في مجلد config/settings.py)
LICENSE_FILE_PATH = 'license.json' 
PUBLIC_KEY_PATH = 'config/public_key.pem' 
"""
lm = License Manager: مسؤول عن توليد Machine ID، والتحقق من التوقيع، وتفعيل البرنامج.
lm-lpk = License Manager - Load Public Key: تحميل المفتاح العام للتحقق من التوقيع.
lm-cas = License Manager - Check Activation Status: التحقق من حالة التفعيل.
lm-af = License Manager - Activate From File: التفعيل من ملف الترخيص.
lm-gcmid = License Manager - Get Current Machine ID: الحصول على معرف الجهاز الحالي.
lm-rlf = License Manager - Read License File: قراءة ملف الترخيص.
lm-vs = License Manager - Verify Signature: التحقق من التوقيع.
lm-uls = License Manager - Update Local License Status: تحديث حالة الترخيص المحلية.
lm-la = License Manager - Log Audit: تسجيل التدقيق.

"""
class LicenseManager:
    """
    مدير الترخيص: مسؤول عن توليد Machine ID، والتحقق من التوقيع، وتفعيل البرنامج.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.public_key = self._load_public_key()

    def _load_public_key(self) -> Optional[Any]:
        print("\n\n🔑 lm-lpk loading public key...")
        """تحميل المفتاح العام المستخدم للتحقق من التوقيع"""
        try:
            with open(PUBLIC_KEY_PATH, "rb") as key_file:
                key_content = key_file.read()
                print("🔑 lm-lpk Public key opened successfully.")
                print("🔑 lm-lpk Public Key Path:", PUBLIC_KEY_PATH)
                print("🔑 lm-lpk Key File Content Preview:", key_content)
                return serialization.load_pem_public_key(key_content)
        except FileNotFoundError:
            # يجب أن يكون المفتاح العام متوفراً دائماً لتشغيل التحقق
            print(f"🔑 lm-lpk Key ERROR: Public key file not found at {PUBLIC_KEY_PATH}")
            self.db.execute_query(
                "INSERT INTO Audit_Logs (timestamp, action_type, details) VALUES (?, ?, ?)",
                (datetime.now().isoformat(), 'LICENSE_ERROR', 'Public Key file missing'),
                commit=True
            )
            return None
        except Exception as e:
            print(f"🔑 lm-lpk Key ERROR: {e}")
            print("🔑 lm-lpk Key ERROR: Failed to load public key.",PUBLIC_KEY_PATH)
            return None

# --- الدوال الرئيسية للتفعيل والتحقق ---

    def check_activation_status(self) -> bool:
        print("\n\n🔑 lm-cas checking activation status...")
        """
        1. التحقق من حالة التفعيل المخزنة محلياً.
        2. إجراء تحقق دوري عبر ملف الترخيص.
        """
        license_info = self.db.get_license_info()
        
        # 1. التحقق من حالة التفعيل في قاعدة البيانات
        if license_info and license_info.get('is_active') == 1:
            expires_at_str = license_info.get('expires_at')
            if expires_at_str:
                if datetime.strptime(expires_at_str, '%Y-%m-%dT%H:%M:%S').date() < date.today():
                    # انتهت صلاحية الترخيص
                    print("🔑 lm-cas License expired.")
                    self._update_local_license_status(is_active=False, status_msg='Expired')
                    return False
            print("🔑 lm-cas License is active and valid." )
            return True # مُفعّل وغير منتهي الصلاحية

        # 2. إذا لم يكن مفعلاً، حاول التفعيل من ملف الترخيص
        return self.activate_from_file()

    def activate_from_file(self) -> bool:
        print("\n\n🔑 lm-af attempting activation from license file...")
        """
        محاولة التفعيل من ملف license.json
        """
        # 0. التحقق من وجود المفتاح العام
        if not self.public_key:
            print("🔑 lm-af ERROR: Public key not loaded, cannot verify license.")
            return False 

        # 1. قراءة بيانات الترخيص من الملف
        license_data = self._read_license_file()
        if not license_data:
            self._log_audit('LICENSE_FAILED', 'License file not found or invalid JSON.')
            print("🔑 lm-af License file not found or invalid.")
            return False

        # 2. التحقق من التوقيع الرقمي (سلامة الملف)
        if not self._verify_signature(license_data):
            self._update_local_license_status(is_active=False, status_msg='Invalid Signature')
            self._log_audit('LICENSE_FAILED', 'Digital signature validation failed (File compromised).')
            print("🔑 lm-af Digital signature validation failed.")
            return False

        # 3. التحقق من تطابق Machine ID
        current_machine_id = self.get_current_machine_id()
        if license_data.get('machine_id') != current_machine_id:
            self._update_local_license_status(is_active=False, status_msg='ID Mismatch')
            self._log_audit('LICENSE_FAILED', f'Machine ID mismatch. License ID: {license_data.get("machine_id")}')
            print("🔑 lm-af Machine ID mismatch.")
            return False

        # 4. التحقق من تاريخ الانتهاء (Expires At)
        print("🔑 lm-af license check", license_data.get('expires_at'))
        print("🔑 lm-af license check",datetime.now())

        if license_data.get('expires_at'):
            print("🔑 lm-af license check", license_data.get('expires_at'))
            if datetime.strptime(license_data.get('expires_at'), '%Y-%m-%dT%H:%M:%S.%f').date() < date.today():
                self._log_audit('LICENSE_FAILED', 'License expired upon verification.')
                print("🔑 lm-af License expired.")

                
        # 5. النجاح: تحديث حالة التفعيل في قاعدة البيانات
        self._update_local_license_status(
            is_active=True, 
            status_msg='Valid',
            license_key=license_data.get('license_key'),
            machine_id_used=current_machine_id,
            issued_at=license_data.get('issued_at'),
            expires_at=license_data.get('expires_at')
        )
        self._log_audit('LICENSE_SUCCESS', f"Program activated successfully with key: {license_data.get('license_key')}")
        
        return True

# --- الدوال المساعدة ---

    def get_current_machine_id(self) -> str:
        """يولد بصمة الجهاز ويخزنها محلياً إذا كانت غير موجودة، ثم يعيد الـ Hash."""
        
        # 1. توليد مكونات البصمة
        data = generate_machine_id_hash() # دالة وهمية، يجب أن تنفذ في machine_fingerprint.py

        # 2. تخزين المعلومات في جدول Device_Info
        self.db.set_device_info({
            'machine_id_hash': data['machine_id_hash'],
            'bios_uuid': data['bios_uuid'],
            'disk_serial': data['disk_serial'],
            'mac_address': data['mac_address'],
        })

        return data['machine_id_hash']

    def _read_license_file(self) -> Optional[Dict]:
        print("\n\n🔑 lm-rlf reading license file...")
        """قراءة ملف license.json محلياً"""
        try:
            with open(LICENSE_FILE_PATH, 'r') as f:
                print("🔑 lm-rlf License file found at:", LICENSE_FILE_PATH)
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"🔑 lm-rlf License file ERROR: Could not read or parse {LICENSE_FILE_PATH}")
            return None

    def _verify_signature(self, license_data: Dict) -> bool:
        print("\n\n🔑 lm-vs verifying digital signature...")
        """
        التحقق من صحة التوقيع الرقمي باستخدام المفتاح العام.
        """
        signature = license_data.pop('signature', "empty")
        if not signature:
            print("🔑 lm-vs Signature missing in license data.")
            return False

        # إعادة بناء البيانات الموقعة (بدون حقل signature)
        data_to_verify = json.dumps(license_data, sort_keys=True).encode('utf-8')

        try:
            self.public_key.verify(
                bytes.fromhex(signature), # تحويل التوقيع من صيغة Hex إلى Bytes
                data_to_verify,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            print("🔑 lm-vs Signature verified successfully.")
            return True
        except Exception as e:
            # يحدث خطأ هنا إذا كان التوقيع غير صالح
            print(f"🔑 lm-vs Verification Error: {e}")
            return False
        
    def _update_local_license_status(self, is_active: bool, status_msg: str, **kwargs):
        """تحديث حالة الترخيص في جدول Licenses"""
        data = {
            'is_active': 1 if is_active else 0,
            'signature_status': status_msg,
            'last_check_date': datetime.now().isoformat(),
        }
        data.update(kwargs) # إضافة المفتاح وتاريخ الإصدار والانتهاء عند التفعيل الناجح
        self.db.set_license_info(data)
        print("data:", data)
        print("🔑 lm-uls License status updated:", self.db.get_license_info())

    def _log_audit(self, action_type: str, details: str, user_id: Optional[int] = None):
        """تسجيل الإجراءات الهامة في جدول Audit_Logs"""
        self.db.execute_query(
            "INSERT INTO Audit_Logs (timestamp, action_type, details, user_id) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), action_type, details, user_id),
            commit=True
        )
