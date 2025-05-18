from PySide6.QtCore import QTranslator, QLocale
from pathlib import Path
import json

class I18nManager:
    def __init__(self):
        self.translator = QTranslator()
        self.current_locale = QLocale.system()
        self.translations = {}
        self.load_translations()
        
    def load_translations(self):
        translations_dir = Path("translations")
        if not translations_dir.exists():
            return
            
        for file in translations_dir.glob("*.json"):
            locale = file.stem
            with open(file, 'r', encoding='utf-8') as f:
                self.translations[locale] = json.load(f)
                
    def set_locale(self, locale: str):
        if locale in self.translations:
            self.current_locale = QLocale(locale)
            if self.translator.load(f":/translations/{locale}"):
                QApplication.installTranslator(self.translator)
                
    def translate(self, key: str, **kwargs) -> str:
        if self.current_locale.name() in self.translations:
            translation = self.translations[self.current_locale.name()].get(key, key)
            return translation.format(**kwargs)
        return key
        
    def format_number(self, number: float) -> str:
        return self.current_locale.toString(number)
        
    def format_currency(self, amount: float) -> str:
        return self.current_locale.toCurrencyString(amount)
        
    def format_date(self, date) -> str:
        return self.current_locale.toString(date) 