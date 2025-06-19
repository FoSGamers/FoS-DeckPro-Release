"""
Main example application demonstrating APTPT features.
Shows how to integrate APTPT into a PySide6 application with monitoring and error handling.
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                              QWidget, QLabel, QSpinBox, QDoubleSpinBox, QGroupBox,
                              QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt, QTimer
import random
import time

from aptpt_pyside6_kit.aptpt import aptpt_wrapper
from aptpt_pyside6_kit.aptpt_error_ui import show_aptpt_error_dialog, show_aptpt_warning
from aptpt_pyside6_kit.aptpt_monitor import APTPTMonitor
from demo_modules import (get_temperature, get_status_vector, risky_division,
                         simulate_network_request, process_data)

class MainWindow(QMainWindow):
    """Main application window demonstrating APTPT features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("APTPT PySide6 Demo")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create demo sections
        self.create_temperature_section(layout)
        self.create_vector_section(layout)
        self.create_error_section(layout)
        self.create_network_section(layout)
        self.create_data_processing_section(layout)
        
        # Add APTPT monitor
        self.aptpt_monitor = APTPTMonitor(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.aptpt_monitor)
        
        # Set up auto-refresh timer for temperature
        self.temp_timer = QTimer()
        self.temp_timer.timeout.connect(self.check_temp)
        self.temp_timer.start(2000)  # Update every 2 seconds
    
    def create_temperature_section(self, parent_layout):
        """Create temperature monitoring section."""
        group = QGroupBox("Temperature Monitoring")
        layout = QVBoxLayout()
        
        # Temperature display
        self.temp_label = QLabel("Current Temperature: --")
        layout.addWidget(self.temp_label)
        
        # Target temperature control
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Target Temperature:"))
        self.target_temp = QDoubleSpinBox()
        self.target_temp.setRange(60, 90)
        self.target_temp.setValue(72)
        self.target_temp.setSuffix(" °F")
        target_layout.addWidget(self.target_temp)
        layout.addLayout(target_layout)
        
        # Threshold control
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Warning Threshold:"))
        self.temp_threshold = QDoubleSpinBox()
        self.temp_threshold.setRange(0.1, 10)
        self.temp_threshold.setValue(2.0)
        self.temp_threshold.setSuffix(" °F")
        threshold_layout.addWidget(self.temp_threshold)
        layout.addLayout(threshold_layout)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_vector_section(self, parent_layout):
        """Create vector monitoring section."""
        group = QGroupBox("Vector Monitoring")
        layout = QVBoxLayout()
        
        # Vector display
        self.vector_label = QLabel("Status Vector: --")
        layout.addWidget(self.vector_label)
        
        # Check button
        self.vec_button = QPushButton("Check Status Vector")
        self.vec_button.clicked.connect(self.check_vec)
        layout.addWidget(self.vec_button)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_error_section(self, parent_layout):
        """Create error testing section."""
        group = QGroupBox("Error Testing")
        layout = QVBoxLayout()
        
        # Division test
        div_layout = QHBoxLayout()
        self.div_x = QSpinBox()
        self.div_x.setRange(1, 100)
        self.div_x.setValue(10)
        self.div_y = QSpinBox()
        self.div_y.setRange(0, 100)
        self.div_y.setValue(2)
        div_layout.addWidget(QLabel("Division:"))
        div_layout.addWidget(self.div_x)
        div_layout.addWidget(QLabel("/"))
        div_layout.addWidget(self.div_y)
        layout.addLayout(div_layout)
        
        # Division button
        self.div_button = QPushButton("Test Division")
        self.div_button.clicked.connect(self.test_division)
        layout.addWidget(self.div_button)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_network_section(self, parent_layout):
        """Create network request testing section."""
        group = QGroupBox("Network Testing")
        layout = QVBoxLayout()
        
        # Timeout control
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout:"))
        self.timeout = QDoubleSpinBox()
        self.timeout.setRange(0.1, 5.0)
        self.timeout.setValue(1.0)
        self.timeout.setSuffix(" s")
        timeout_layout.addWidget(self.timeout)
        layout.addLayout(timeout_layout)
        
        # Network button
        self.network_button = QPushButton("Test Network Request")
        self.network_button.clicked.connect(self.test_network)
        layout.addWidget(self.network_button)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def create_data_processing_section(self, parent_layout):
        """Create data processing testing section."""
        group = QGroupBox("Data Processing")
        layout = QVBoxLayout()
        
        # Data input
        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel("Data Points:"))
        self.data_points = QSpinBox()
        self.data_points.setRange(5, 100)
        self.data_points.setValue(20)
        data_layout.addWidget(self.data_points)
        layout.addLayout(data_layout)
        
        # Process button
        self.process_button = QPushButton("Process Data")
        self.process_button.clicked.connect(self.test_processing)
        layout.addWidget(self.process_button)
        
        group.setLayout(layout)
        parent_layout.addWidget(group)
    
    def check_temp(self):
        """Check temperature with APTPT monitoring."""
        try:
            target = self.target_temp.value()
            threshold = self.temp_threshold.value()
            result = aptpt_wrapper(target, get_temperature, threshold=threshold)
            self.temp_label.setText(f"Current Temperature: {result:.1f}°F (Target: {target}°F)")
        except Exception as e:
            show_aptpt_error_dialog(self, "check_temp", "Failed to get temperature", {}, e)
    
    def check_vec(self):
        """Check status vector with APTPT monitoring."""
        try:
            target = [1.0, 0.0, -0.1]
            result = aptpt_wrapper(target, get_status_vector)
            self.vector_label.setText(f"Status Vector: {[f'{x:.2f}' for x in result]}")
        except Exception as e:
            show_aptpt_error_dialog(self, "check_vec", "Failed to get status vector", {}, e)
    
    def test_division(self):
        """Test division with APTPT monitoring."""
        try:
            x = self.div_x.value()
            y = self.div_y.value()
            target = x / y if y != 0 else None
            result = aptpt_wrapper(target, risky_division, x, y)
            QMessageBox.information(self, "Division Result", f"Result: {result}")
        except Exception as e:
            show_aptpt_error_dialog(self, "test_division", "Division failed", 
                                  {"x": x, "y": y}, e)
    
    def test_network(self):
        """Test network request with APTPT monitoring."""
        try:
            timeout = self.timeout.value()
            target = {"status": "success"}
            result = aptpt_wrapper(target, simulate_network_request, timeout)
            QMessageBox.information(self, "Network Result", 
                                  f"Request successful: {result}")
        except Exception as e:
            show_aptpt_error_dialog(self, "test_network", "Network request failed",
                                  {"timeout": timeout}, e)
    
    def test_processing(self):
        """Test data processing with APTPT monitoring."""
        try:
            n_points = self.data_points.value()
            data = [random.gauss(100, 10) for _ in range(n_points)]
            target = {"count": n_points}
            result = aptpt_wrapper(target, process_data, data)
            QMessageBox.information(self, "Processing Result",
                                  f"Processed {result['count']} points\n"
                                  f"Mean: {result['mean']:.2f}\n"
                                  f"Std Dev: {result['std_dev']:.2f}\n"
                                  f"Outliers: {len(result['outliers'])}")
        except Exception as e:
            show_aptpt_error_dialog(self, "test_processing", "Data processing failed",
                                  {"n_points": n_points}, e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 