# محتوى مقترح لملف utils/machine_fingerprint.py
from ast import Dict
import platform
import hashlib
import uuid
from datetime import datetime
# قد تحتاج إلى مكتبات إضافية مثل 'wmi' لنظام Windows أو 'psutil'

def generate_machine_id_hash() -> Dict[str, str]:
    """
    يجمع خصائص الجهاز ويُنشئ بصمة SHA256 النهائية.
    """
    
    # 1. جمع الخصائص
    try:
        # مثال على الحصول على البيانات
        disk_serial = "D-12345-ABC" # يجب استبدالها باستدعاء مكتبة النظام الحقيقي
        bios_uuid = platform.node() + "-" + str(uuid.getnode()) 
        mac_address = hex(uuid.getnode())
        current_year = int(datetime.now().year)+50
        # 2. دمج الخصائص
        raw_fingerprint = f"{bios_uuid}|{disk_serial}|{mac_address}|{current_year}"

        # 3. حساب الـ SHA256
        machine_id_hash = hashlib.sha256(raw_fingerprint.encode('utf-8')).hexdigest()

    except Exception as e:
        # في حالة فشل أي استدعاء لنظام التشغيل، نعتمد على شيء أساسي
        machine_id_hash = hashlib.sha256(platform.node().encode('utf-8')).hexdigest()
        disk_serial = "N/A"
        bios_uuid = "N/A"
        mac_address = "N/A"
        current_year = "N/A"


    return {
        'machine_id_hash': machine_id_hash,
        'bios_uuid': bios_uuid,
        'disk_serial': disk_serial,
        'mac_address': mac_address,
        'current_year': str(current_year)
    }
