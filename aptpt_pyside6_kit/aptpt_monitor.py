"""
Live error log and system state monitor widget for APTPT.
Provides a dockable widget for real-time monitoring of system state and errors.
"""

from PySide6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QLabel, 
                              QTextEdit, QPushButton, QHBoxLayout)
from PySide6.QtCore import Qt, QTimer
import os
import json
from datetime import datetime

class APTPTMonitor(QDockWidget):
    """Dockable widget for monitoring APTPT events and system state."""
    
    def __init__(self, parent=None):
        super().__init__("APTPT System Monitor", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        
        # Create main widget and layout
        self.widget = QWidget()
        self.layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        self.title_label = QLabel("APTPT System Monitor")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.refresh_button)
        self.layout.addLayout(header_layout)
        
        # Status summary
        self.status_label = QLabel("System Status: Normal")
        self.status_label.setStyleSheet("color: green;")
        self.layout.addWidget(self.status_label)
        
        # Event log
        self.log_label = QLabel("Recent Events:")
        self.logbox = QTextEdit()
        self.logbox.setReadOnly(True)
        self.logbox.setMinimumHeight(200)
        self.layout.addWidget(self.log_label)
        self.layout.addWidget(self.logbox)
        
        # Set up auto-refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)  # Refresh every 5 seconds
        
        # Set up the widget
        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)
        
        # Initial refresh
        self.refresh()
    
    def refresh(self):
        """Refresh the monitor display with latest events."""
        log_file = "aptpt_error_log.jsonl"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = f.readlines()[-30:]  # Show last 30 events
            
            # Parse and format logs
            formatted_logs = []
            error_count = 0
            warning_count = 0
            
            for log in logs:
                try:
                    entry = json.loads(log)
                    timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
                    level = entry["level"]
                    event = entry["event"]
                    desc = entry["description"]
                    
                    if level == "ERROR":
                        error_count += 1
                        color = "red"
                    elif level == "WARN":
                        warning_count += 1
                        color = "orange"
                    else:
                        color = "black"
                    
                    formatted_logs.append(
                        f'<span style="color: {color}">[{timestamp}] {level}: {event} - {desc}</span>'
                    )
                except json.JSONDecodeError:
                    continue
            
            # Update display
            self.logbox.setHtml("<br>".join(formatted_logs))
            
            # Update status
            if error_count > 0:
                self.status_label.setText(f"System Status: Error ({error_count} errors, {warning_count} warnings)")
                self.status_label.setStyleSheet("color: red;")
            elif warning_count > 0:
                self.status_label.setText(f"System Status: Warning ({warning_count} warnings)")
                self.status_label.setStyleSheet("color: orange;")
            else:
                self.status_label.setText("System Status: Normal")
                self.status_label.setStyleSheet("color: green;")
        else:
            self.logbox.setText("No logs available.")
            self.status_label.setText("System Status: No Data")
            self.status_label.setStyleSheet("color: gray;")
    
    def showEvent(self, event):
        """Handle widget show event."""
        self.refresh()
        super().showEvent(event)
    
    def closeEvent(self, event):
        """Handle widget close event."""
        self.timer.stop()
        super().closeEvent(event) 