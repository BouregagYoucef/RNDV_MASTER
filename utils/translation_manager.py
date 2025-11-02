from typing import Dict, Optional
from db.database_manager import DatabaseManager 
from config.settings import DEFAULT_LANGUAGE 


"""
TraM-load   Translation Manager loads_translations
TranM-set   Translation Manager set_language.
TranM-get   Translation Manager get_text.
TraM-get_all   Translation Manager get_all_translations.
"""
class TranslationManager:
    """
    مسؤول عن تحميل وإدارة نصوص الترجمة.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager
        self._translations: Dict[str, Dict[str, str]] = {}
        self._current_language = DEFAULT_LANGUAGE
        
        # 1. تحميل الترجمات من DB
        self.load_translations()
        
        # 2. تعيين اللغة من الإعدادات المخزنة (بعد تهيئة DB)
        settings = self._db.get_settings()
        if settings and settings.get('language'):
            self._current_language = settings['language']

    def load_translations(self):
        """تحميل جميع نصوص الترجمة من قاعدة البيانات."""
        try:
            self._translations = self._db.get_translations()
        except Exception as e:
            print(f"TraM-load ❌ Error loading translations from DB: {e}")
            self._translations = {}

    def set_language(self, lang_code: str):
        """تغيير اللغة الحالية للتطبيق وحفظها في قاعدة البيانات."""
        if lang_code in ['ar', 'fr']:
            self._current_language = lang_code
            # تحديث اللغة في جدول Settings
            self._db.update_settings({'language': lang_code})

    def get_language(self) -> str:
        """إرجاع اللغة الحالية."""
        return self._current_language

    def get_text(self, key: str, default_text: str = "TEXT_MISSING") -> str:
        """
        استرداد النص المترجم بناءً على المفتاح (key) واللغة الحالية.
        """
        key_translations = self._translations.get(key, {})
        text = key_translations.get(self._current_language)
        
        if text:
            return text
        
        return default_text
    def get_all_translations(self) -> Dict[str, Dict[str, str]]:
        """إرجاع جميع الترجمات المحملة."""
        print("TraM-get_all ✅ Returning all translations.")
        print(self._translations)
        return self._translations