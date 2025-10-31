from typing import Dict, Optional
from db.database_manager import DatabaseManager # استيراد مدير قاعدة البيانات
from config.settings import DEFAULT_LANGUAGE # استيراد اللغة الافتراضية من ملف settings.py

class TranslationManager:
    """
    مسؤول عن تحميل وإدارة نصوص الترجمة.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager
        self._translations: Dict[str, Dict[str, str]] = {}
        self._current_language = DEFAULT_LANGUAGE
        self.load_translations()

    def load_translations(self):
        """
        تحميل جميع نصوص الترجمة من قاعدة البيانات (جدول Translations).
        يتم تخزينها في الذاكرة لتجنب استدعاء DB متكرر.
        """
        try:
            self._translations = self._db.get_translations()
        except Exception as e:
            print(f"Error loading translations from DB: {e}")
            # في حالة الفشل، يتم تعيين قاموس فارغ
            self._translations = {}

    def set_language(self, lang_code: str):
        """تغيير اللغة الحالية للتطبيق."""
        if lang_code in ['ar', 'fr']:
            self._current_language = lang_code
            # يمكنك هنا إضافة منطق لحفظ اللغة الجديدة في جدول Settings

    def get_language(self) -> str:
        """إرجاع اللغة الحالية."""
        return self._current_language

    def get_text(self, key: str, default_text: str = "TEXT_MISSING") -> str:
        """
        استرداد النص المترجم بناءً على المفتاح (key) واللغة الحالية.

        :param key: مفتاح النص البرمجي (مثال: 'dashboard_title').
        :param default_text: النص البديل في حالة عدم العثور على المفتاح أو النص.
        :return: النص المترجم.
        """
        # 1. البحث عن المفتاح في القاموس
        key_translations = self._translations.get(key, {})
        
        # 2. استرداد النص للغة الحالية
        text = key_translations.get(self._current_language)
        
        # 3. إذا لم يتم العثور عليه، نعود للنص الافتراضي
        if text:
            return text
        
        # 4. إذا لم يتم العثور عليه، نعود للنص الافتراضي
        return default_text
    
# ملاحظة: عند بدء التشغيل، يجب أن تقوم بإضافة بعض النصوص الافتراضية
# إلى جدول Translations يدويًا عبر SQL أو من خلال دالة في DatabaseManager.
