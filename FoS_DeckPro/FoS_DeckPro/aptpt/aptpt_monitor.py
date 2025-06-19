from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTextEdit,
    QPushButton, QHBoxLayout, QLabel, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from typing import Dict, Any, List
import json
from datetime import datetime
from .aptpt import log_aptpt_event

class APTPTMonitor(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("APTPT Monitor", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        
        # Create main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Add status summary
        self.status_label = QLabel("System Status: Normal")
        layout.addWidget(self.status_label)
        
        # Add filter controls
        filter_layout = QHBoxLayout()
        
        self.level_filter = QComboBox()
        self.level_filter.addItems(["All", "Error", "Warning", "Info", "Performance", "Adaptive"])
        self.level_filter.currentTextChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("Level:"))
        filter_layout.addWidget(self.level_filter)
        
        self.function_filter = QComboBox()
        self.function_filter.addItems(["All"])
        self.function_filter.currentTextChanged.connect(self.refresh)
        filter_layout.addWidget(QLabel("Function:"))
        filter_layout.addWidget(self.function_filter)
        
        layout.addLayout(filter_layout)
        
        # Add log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        # Add control buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
        
        # Set main widget
        self.setWidget(main_widget)
        
        # Setup refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        
        # Initialize state
        self.last_refresh = datetime.now()
        self.error_count = 0
        self.warning_count = 0
        
        # Initial refresh
        self.refresh()
        
        # Log monitor creation
        log_aptpt_event(
            'info',
            'APTPT Monitor created',
            {'timestamp': self.last_refresh.isoformat()}
        )

    def refresh(self) -> None:
        """Refresh the monitor display."""
        try:
            # Read log file
            events = []
            try:
                with open('aptpt_error_log.jsonl', 'r') as f:
                    for line in f:
                        try:
                            event = json.loads(line)
                            events.append(event)
                        except json.JSONDecodeError:
                            continue
            except FileNotFoundError:
                pass
            
            # Filter events
            level_filter = self.level_filter.currentText()
            function_filter = self.function_filter.currentText()
            
            filtered_events = []
            for event in events:
                if level_filter != "All" and event['level'] != level_filter:
                    continue
                if function_filter != "All" and event.get('function') != function_filter:
                    continue
                filtered_events.append(event)
            
            # Update function filter
            functions = set()
            for event in events:
                if 'function' in event:
                    functions.add(event['function'])
            self.function_filter.clear()
            self.function_filter.addItems(["All"] + sorted(list(functions)))
            
            # Update status
            self.error_count = sum(1 for e in events if e['level'] == 'error')
            self.warning_count = sum(1 for e in events if e['level'] == 'warning')
            
            if self.error_count > 0:
                self.status_label.setText(f"System Status: Error ({self.error_count} errors, {self.warning_count} warnings)")
                self.status_label.setStyleSheet("color: red;")
            elif self.warning_count > 0:
                self.status_label.setText(f"System Status: Warning ({self.warning_count} warnings)")
                self.status_label.setStyleSheet("color: orange;")
            else:
                self.status_label.setText("System Status: Normal")
                self.status_label.setStyleSheet("")
            
            # Update log display
            self.log_display.clear()
            for event in filtered_events[-100:]:  # Show last 100 events
                timestamp = datetime.fromisoformat(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                level = event['level'].upper()
                message = event['description']
                
                if 'function' in event:
                    message = f"[{event['function']}] {message}"
                
                if 'variables' in event and event['variables']:
                    message += f"\nVariables: {json.dumps(event['variables'], indent=2)}"
                
                if 'exception' in event:
                    message += f"\nException: {event['exception']['type']}: {event['exception']['message']}"
                    message += f"\n{event['exception']['traceback']}"
                
                self.log_display.append(f"[{timestamp}] {level}: {message}\n")
            
            # Scroll to bottom
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )
            
            # Update last refresh time
            self.last_refresh = datetime.now()
            
        except Exception as e:
            log_aptpt_event(
                'error',
                'Failed to refresh APTPT Monitor',
                {'error': str(e)}
            )

    def clear_log(self) -> None:
        """Clear the log file."""
        try:
            with open('aptpt_error_log.jsonl', 'w') as f:
                pass
            self.refresh()
            
            log_aptpt_event(
                'info',
                'APTPT Monitor log cleared',
                {'timestamp': datetime.now().isoformat()}
            )
        except Exception as e:
            log_aptpt_event(
                'error',
                'Failed to clear APTPT Monitor log',
                {'error': str(e)}
            )

    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        self.refresh()

    def closeEvent(self, event) -> None:
        """Handle close event."""
        self.refresh_timer.stop()
        super().closeEvent(event) 