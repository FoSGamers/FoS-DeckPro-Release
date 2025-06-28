from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QScrollArea, QWidget
from PySide6.QtCore import Qt
import json
import csv

class PackingSlipSummaryDialog(QDialog):
    def __init__(self, summary, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Packing Slip Processing Summary")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        # Cards removed
        removed = summary.get('removed', [])
        not_found = summary.get('not_found', [])
        ambiguous = summary.get('ambiguous', [])
        buyers = summary.get('buyers', [])
        files = summary.get('files', [])
        errors = summary.get('errors', [])
        def add_section(title, items, formatter):
            if not items:
                return
            content_layout.addWidget(QLabel(f"<b>{title}</b> ({len(items)})"))
            txt = QTextEdit()
            txt.setReadOnly(True)
            txt.setPlainText("\n".join(formatter(i) for i in items))
            txt.setMinimumHeight(min(200, 30 + 20 * len(items)))
            content_layout.addWidget(txt)
        add_section("Cards Removed", removed, lambda i: f"{i['sale'].get('Name','')} x{i['sale'].get('Quantity','')} (matched: {i['match'].get('Set code','') if i.get('match') else ''}) {i.get('reason','')}")
        add_section("Not Found", not_found, lambda i: f"{i['sale'].get('Name','')} x{i['sale'].get('Quantity','')} - {i['reason']}")
        add_section("Ambiguous", ambiguous, lambda i: f"{i['sale'].get('Name','')} x{i['sale'].get('Quantity','')} - {i['reason']}")
        add_section("Buyers Updated", buyers, lambda i: f"{i['name']} ({i['username']}) - {i['total_cards']} cards, ${i['total_spent']:.2f} total")
        add_section("Files Processed", files, lambda i: i)
        add_section("Errors", errors, lambda i: i)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        # Export buttons
        btns = QHBoxLayout()
        export_csv = QPushButton("Export CSV")
        export_json = QPushButton("Export JSON")
        close_btn = QPushButton("Close")
        btns.addWidget(export_csv)
        btns.addWidget(export_json)
        btns.addWidget(close_btn)
        layout.addLayout(btns)
        export_csv.clicked.connect(lambda: self.export_summary(summary, 'csv'))
        export_json.clicked.connect(lambda: self.export_summary(summary, 'json'))
        close_btn.clicked.connect(self.accept)
    def export_summary(self, summary, fmt):
        if fmt == 'json':
            path, _ = QFileDialog.getSaveFileName(self, "Export Summary as JSON", "packing_slip_summary.json", "JSON Files (*.json)")
            if not path:
                return
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2)
                QMessageBox.information(self, "Export", f"Summary exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e))
        else:
            path, _ = QFileDialog.getSaveFileName(self, "Export Summary as CSV", "packing_slip_summary.csv", "CSV Files (*.csv)")
            if not path:
                return
            try:
                # Flatten and write removed, not_found, ambiguous, buyers, files, errors
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for key in ['removed', 'not_found', 'ambiguous', 'buyers', 'files', 'errors']:
                        items = summary.get(key, [])
                        writer.writerow([key.upper()])
                        if key == 'buyers':
                            writer.writerow(['Name', 'Username', 'Total Cards', 'Total Spent'])
                            for b in items:
                                writer.writerow([b.get('name',''), b.get('username',''), b.get('total_cards',0), b.get('total_spent',0)])
                        elif key == 'files':
                            writer.writerow(['File'])
                            for i in items:
                                writer.writerow([i])
                        elif key == 'errors':
                            writer.writerow(['Error'])
                            for i in items:
                                writer.writerow([i])
                        else:
                            writer.writerow(['Name', 'Quantity', 'Reason'])
                            for i in items:
                                writer.writerow([i['sale'].get('Name',''), i['sale'].get('Quantity',''), i.get('reason','')])
                        writer.writerow([])
                QMessageBox.information(self, "Export", f"Summary exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", str(e)) 