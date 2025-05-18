from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from config import Config
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import shutil

class OutputGenerator:
    def __init__(self):
        self.config = Config
        self.supported_formats = {'dck', 'txt', 'csv', 'pdf'}

    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename)
        
    def _validate_deck_structure(self, deck_obj: Dict[str, Any]) -> bool:
        """Validate deck object has required fields"""
        required_fields = {'mainboard', 'stats', 'commander'}
        return all(field in deck_obj for field in required_fields)

    def generate_deck_file(self, deck_obj: dict, file_path: str, format: str = "dck") -> bool:
        try:
            if not self._validate_deck_structure(deck_obj):
                raise ValueError("Invalid deck structure")
                
            if format not in self.supported_formats:
                raise ValueError(f"Unsupported format: {format}")
                
            file_path = Path(self._sanitize_filename(file_path))
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use temporary file for atomic write
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp:
                if format == 'dck':
                    self._write_dck_format(deck_obj, temp)
                elif format == 'txt':
                    self._write_txt_format(deck_obj, temp)
                elif format == 'csv':
                    self._write_csv_format(deck_obj, temp)
                    
                temp_path = temp.name
                
            # Atomic move
            shutil.move(temp_path, file_path)
            return True
            
        except Exception as e:
            print(f"Error generating deck file: {e}")
            if 'temp_path' in locals():
                os.unlink(temp_path)
            return False

    def generate_batch_simulation_report_pdf_or_csv(self, aggregated_sim_results: list, deck_tested_name: str, file_path: str) -> bool:
        try:
            if not aggregated_sim_results:
                raise ValueError("No simulation results provided")
                
            file_path = Path(self._sanitize_filename(file_path))
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use temporary file for atomic write
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp_path = temp.name
                
                if file_path.suffix.lower() == '.pdf':
                    self._generate_pdf_report(aggregated_sim_results, deck_tested_name, temp_path)
                else:
                    self._generate_csv_report(aggregated_sim_results, deck_tested_name, temp_path)
                    
            # Atomic move
            shutil.move(temp_path, file_path)
            return True
            
        except Exception as e:
            print(f"Error generating report: {e}")
            if 'temp_path' in locals():
                os.unlink(temp_path)
            return False

    def generate_sales_description(self, deck_obj: dict) -> Optional[str]:
        try:
            if not self._validate_deck_structure(deck_obj):
                return None
                
            format_type = deck_obj["stats"]["format"]
            template = self.config.SALES_DESCRIPTION_TEMPLATES.get(format_type)
            
            if not template:
                return None
                
            # Validate template placeholders
            required_fields = {'commander', 'archetype', 'card_count', 'price'}
            if not all(f"{{{field}}}" in template for field in required_fields):
                return None
                
            return template.format(
                commander=deck_obj["commander"]["name"] if deck_obj["commander"] else "No Commander",
                archetype=deck_obj["stats"]["archetype"],
                card_count=sum(count for _, count in deck_obj["mainboard"]),
                price=deck_obj["stats"]["total_cost"] * (1 + self.config.PROFIT_MARGIN)
            )
            
        except Exception as e:
            print(f"Error generating sales description: {e}")
            return None
