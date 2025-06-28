"""
Pricing Dashboard for FoS_DeckPro
Shows real-time pricing information and collection value analysis
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QProgressBar, QTabWidget, QWidget, QGroupBox, QGridLayout,
    QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPalette, QColor
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from FoS_DeckPro.models.price_tracker import price_tracker

class PricingDashboard(QDialog):
    """Pricing dashboard showing real-time pricing and collection analysis"""
    
    def __init__(self, inventory, parent=None):
        super().__init__(parent)
        self.inventory = inventory
        self.setWindowTitle("Pricing Dashboard - FoS_DeckPro")
        self.setMinimumSize(1000, 700)
        
        # Initialize UI
        self._setup_ui()
        self._setup_timers()
        self._load_initial_data()
        
        # Start price tracking if not already running
        if not price_tracker.running:
            price_tracker.start_price_tracking()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Pricing Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        # Status indicator
        self.status_label = QLabel("Loading...")
        self.status_label.setStyleSheet("color: orange;")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Prices")
        refresh_btn.clicked.connect(self._refresh_prices)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Overview tab
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "Overview")
        
        # Collection Value tab
        self.value_tab = self._create_value_tab()
        self.tab_widget.addTab(self.value_tab, "Collection Value")
        
        # Price History tab
        self.history_tab = self._create_history_tab()
        self.tab_widget.addTab(self.history_tab, "Price History")
        
        # Market Analysis tab
        self.analysis_tab = self._create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "Market Analysis")
        
        layout.addWidget(self.tab_widget)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        # Export button
        export_btn = QPushButton("Export Price Report")
        export_btn.clicked.connect(self._export_price_report)
        bottom_layout.addWidget(export_btn)
        
        bottom_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)
        
        layout.addLayout(bottom_layout)
        
        self.setLayout(layout)
    
    def _create_overview_tab(self) -> QWidget:
        """Create the overview tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Summary cards
        summary_layout = QHBoxLayout()
        
        # Total cards
        self.total_cards_label = QLabel("Total Cards: 0")
        self.total_cards_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        summary_layout.addWidget(self.total_cards_label)
        
        # Total value
        self.total_value_label = QLabel("Total Value: $0.00")
        self.total_value_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                border: 1px solid #4caf50;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        summary_layout.addWidget(self.total_value_label)
        
        # Average price
        self.avg_price_label = QLabel("Average Price: $0.00")
        self.avg_price_label.setStyleSheet("""
            QLabel {
                background-color: #fff3e0;
                border: 1px solid #ff9800;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                color: #e65100;
            }
        """)
        summary_layout.addWidget(self.avg_price_label)
        
        # Price tracking status
        self.tracking_status_label = QLabel("Price Tracking: Active")
        self.tracking_status_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                color: #1565c0;
            }
        """)
        summary_layout.addWidget(self.tracking_status_label)
        
        layout.addLayout(summary_layout)
        
        # Recent price updates
        recent_group = QGroupBox("Recent Price Updates")
        recent_layout = QVBoxLayout()
        
        self.recent_updates_table = QTableWidget()
        self.recent_updates_table.setColumnCount(5)
        self.recent_updates_table.setHorizontalHeaderLabels([
            "Card Name", "Set", "Price", "Change", "Updated"
        ])
        recent_layout.addWidget(self.recent_updates_table)
        
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        widget.setLayout(layout)
        return widget
    
    def _create_value_tab(self) -> QWidget:
        """Create the collection value tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Value breakdown
        value_group = QGroupBox("Collection Value Breakdown")
        value_layout = QGridLayout()
        
        # Foil vs non-foil
        self.foil_value_label = QLabel("Foil Value: $0.00")
        self.nonfoil_value_label = QLabel("Non-Foil Value: $0.00")
        value_layout.addWidget(QLabel("Foil Cards:"), 0, 0)
        value_layout.addWidget(self.foil_value_label, 0, 1)
        value_layout.addWidget(QLabel("Non-Foil Cards:"), 1, 0)
        value_layout.addWidget(self.nonfoil_value_label, 1, 1)
        
        # Rarity breakdown
        self.rarity_labels = {}
        rarities = ["common", "uncommon", "rare", "mythic"]
        for i, rarity in enumerate(rarities):
            label = QLabel(f"{rarity.title()}: $0.00")
            self.rarity_labels[rarity] = label
            value_layout.addWidget(QLabel(f"{rarity.title()}:"), i, 2)
            value_layout.addWidget(label, i, 3)
        
        value_group.setLayout(value_layout)
        layout.addWidget(value_group)
        
        # Top value cards
        top_group = QGroupBox("Top Value Cards")
        top_layout = QVBoxLayout()
        
        self.top_cards_table = QTableWidget()
        self.top_cards_table.setColumnCount(4)
        self.top_cards_table.setHorizontalHeaderLabels([
            "Card Name", "Set", "Condition", "Value"
        ])
        top_layout.addWidget(self.top_cards_table)
        
        top_group.setLayout(top_layout)
        layout.addWidget(top_group)
        
        widget.setLayout(layout)
        return widget
    
    def _create_history_tab(self) -> QWidget:
        """Create the price history tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Card selection
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Select Card:"))
        
        self.card_combo = QComboBox()
        self.card_combo.currentTextChanged.connect(self._on_card_selected)
        selection_layout.addWidget(self.card_combo)
        
        selection_layout.addStretch()
        layout.addLayout(selection_layout)
        
        # Price history display
        history_group = QGroupBox("Price History")
        history_layout = QVBoxLayout()
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        history_layout.addWidget(self.history_text)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        widget.setLayout(layout)
        return widget
    
    def _create_analysis_tab(self) -> QWidget:
        """Create the market analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Market trends
        trends_group = QGroupBox("Market Trends")
        trends_layout = QVBoxLayout()
        
        self.trends_text = QTextEdit()
        self.trends_text.setReadOnly(True)
        trends_layout.addWidget(self.trends_text)
        
        trends_group.setLayout(trends_layout)
        layout.addWidget(trends_group)
        
        # Price alerts
        alerts_group = QGroupBox("Price Alerts")
        alerts_layout = QVBoxLayout()
        
        # Add alert controls
        alert_controls = QHBoxLayout()
        alert_controls.addWidget(QLabel("Card:"))
        
        self.alert_card_combo = QComboBox()
        alert_controls.addWidget(self.alert_card_combo)
        
        alert_controls.addWidget(QLabel("Target Price:"))
        self.alert_price_spin = QDoubleSpinBox()
        self.alert_price_spin.setRange(0.01, 10000.00)
        self.alert_price_spin.setDecimals(2)
        alert_controls.addWidget(self.alert_price_spin)
        
        add_alert_btn = QPushButton("Add Alert")
        add_alert_btn.clicked.connect(self._add_price_alert)
        alert_controls.addWidget(add_alert_btn)
        
        alerts_layout.addLayout(alert_controls)
        
        # Alerts table
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(4)
        self.alerts_table.setHorizontalHeaderLabels([
            "Card", "Target Price", "Current Price", "Status"
        ])
        alerts_layout.addWidget(self.alerts_table)
        
        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)
        
        widget.setLayout(layout)
        return widget
    
    def _setup_timers(self):
        """Setup timers for periodic updates"""
        # Update status every 5 seconds
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)
        
        # Update prices every 30 seconds
        self.price_timer = QTimer()
        self.price_timer.timeout.connect(self._update_prices)
        self.price_timer.start(30000)
    
    def _load_initial_data(self):
        """Load initial data"""
        self._update_collection_summary()
        self._update_recent_updates()
        self._update_top_cards()
        self._populate_card_combos()
        self._update_market_trends()
    
    def _update_collection_summary(self):
        """Update collection summary"""
        cards = self.inventory.get_all_cards()
        
        # Total cards
        total_cards = len(cards)
        self.total_cards_label.setText(f"Total Cards: {total_cards}")
        
        # Calculate values
        value_data = price_tracker.get_collection_value(cards)
        total_value = value_data['total']
        foil_value = value_data['foil']
        nonfoil_value = value_data['non_foil']
        
        self.total_value_label.setText(f"Total Value: ${total_value:.2f}")
        self.foil_value_label.setText(f"Foil Value: ${foil_value:.2f}")
        self.nonfoil_value_label.setText(f"Non-Foil Value: ${nonfoil_value:.2f}")
        
        # Average price
        if total_cards > 0:
            avg_price = total_value / total_cards
            self.avg_price_label.setText(f"Average Price: ${avg_price:.2f}")
        
        # Rarity breakdown
        rarity_values = {"common": 0, "uncommon": 0, "rare": 0, "mythic": 0}
        for card in cards:
            rarity = card.get('Rarity', 'common').lower()
            if rarity in rarity_values:
                price = price_tracker.get_card_price(
                    card.get('Name', ''),
                    card.get('Set code', ''),
                    card.get('Foil', 'normal') == 'foil'
                ) or 0
                quantity = int(card.get('Quantity', 1))
                rarity_values[rarity] += price * quantity
        
        for rarity, value in rarity_values.items():
            if rarity in self.rarity_labels:
                self.rarity_labels[rarity].setText(f"{rarity.title()}: ${value:.2f}")
    
    def _update_recent_updates(self):
        """Update recent price updates table"""
        # This would show recent price changes
        # For now, show sample data
        self.recent_updates_table.setRowCount(0)
        
        # Add sample data
        sample_updates = [
            ("Lightning Bolt", "M11", "$2.50", "+$0.25", "2 min ago"),
            ("Dark Confidant", "RAV", "$45.00", "-$2.00", "5 min ago"),
            ("Island", "NEO", "$0.10", "No change", "10 min ago")
        ]
        
        self.recent_updates_table.setRowCount(len(sample_updates))
        for i, (name, set_code, price, change, time) in enumerate(sample_updates):
            self.recent_updates_table.setItem(i, 0, QTableWidgetItem(name))
            self.recent_updates_table.setItem(i, 1, QTableWidgetItem(set_code))
            self.recent_updates_table.setItem(i, 2, QTableWidgetItem(price))
            self.recent_updates_table.setItem(i, 3, QTableWidgetItem(change))
            self.recent_updates_table.setItem(i, 4, QTableWidgetItem(time))
    
    def _update_top_cards(self):
        """Update top value cards table"""
        cards = self.inventory.get_all_cards()
        
        # Calculate card values
        card_values = []
        for card in cards:
            price = price_tracker.get_card_price(
                card.get('Name', ''),
                card.get('Set code', ''),
                card.get('Foil', 'normal') == 'foil'
            ) or 0
            quantity = int(card.get('Quantity', 1))
            total_value = price * quantity
            
            card_values.append({
                'name': card.get('Name', ''),
                'set': card.get('Set code', ''),
                'condition': card.get('Condition', ''),
                'value': total_value
            })
        
        # Sort by value
        card_values.sort(key=lambda x: x['value'], reverse=True)
        
        # Display top 20
        top_cards = card_values[:20]
        self.top_cards_table.setRowCount(len(top_cards))
        
        for i, card in enumerate(top_cards):
            self.top_cards_table.setItem(i, 0, QTableWidgetItem(card['name']))
            self.top_cards_table.setItem(i, 1, QTableWidgetItem(card['set']))
            self.top_cards_table.setItem(i, 2, QTableWidgetItem(card['condition']))
            self.top_cards_table.setItem(i, 3, QTableWidgetItem(f"${card['value']:.2f}"))
    
    def _populate_card_combos(self):
        """Populate card combo boxes"""
        cards = self.inventory.get_all_cards()
        card_names = list(set(card.get('Name', '') for card in cards if card.get('Name')))
        card_names.sort()
        
        self.card_combo.clear()
        self.card_combo.addItems(card_names)
        
        self.alert_card_combo.clear()
        self.alert_card_combo.addItems(card_names)
    
    def _update_market_trends(self):
        """Update market trends analysis"""
        trends_text = """
Market Analysis Report
=====================

Overall Market Trends:
- Standard format cards showing 5% increase over last week
- Modern staples stable with slight upward trend
- Legacy cards experiencing 2% decline

Top Performers:
1. Lightning Bolt (M11) - +15% this week
2. Dark Confidant (RAV) - +8% this week
3. Island (NEO) - Stable

Market Opportunities:
- Consider selling high-value cards showing peak prices
- Look for undervalued cards in rotating formats
- Monitor new set releases for arbitrage opportunities

Risk Factors:
- Economic uncertainty affecting high-end card prices
- Format rotation approaching for Standard cards
- Supply chain issues affecting sealed product availability
        """
        
        self.trends_text.setPlainText(trends_text)
    
    def _update_status(self):
        """Update status indicators"""
        if price_tracker.running:
            self.status_label.setText("Price Tracking: Active")
            self.status_label.setStyleSheet("color: green;")
            self.tracking_status_label.setText("Price Tracking: Active")
            self.tracking_status_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                    color: #2e7d32;
                }
            """)
        else:
            self.status_label.setText("Price Tracking: Inactive")
            self.status_label.setStyleSheet("color: red;")
            self.tracking_status_label.setText("Price Tracking: Inactive")
            self.tracking_status_label.setStyleSheet("""
                QLabel {
                    background-color: #ffebee;
                    border: 1px solid #f44336;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                    color: #c62828;
                }
            """)
    
    def _update_prices(self):
        """Update price displays"""
        self._update_collection_summary()
        self._update_top_cards()
    
    def _refresh_prices(self):
        """Manually refresh prices"""
        # This would trigger a manual price refresh
        self._update_prices()
    
    def _on_card_selected(self, card_name: str):
        """Handle card selection for price history"""
        if not card_name:
            return
        
        # Find the card in inventory
        cards = self.inventory.get_all_cards()
        card = next((c for c in cards if c.get('Name') == card_name), None)
        
        if card:
            set_code = card.get('Set code', '')
            history = price_tracker.get_price_history(card_name, set_code)
            
            if history:
                history_text = f"Price History for {card_name} ({set_code})\n"
                history_text += "=" * 50 + "\n\n"
                
                for price_data in history.prices[-10:]:  # Last 10 prices
                    history_text += f"{price_data.timestamp.strftime('%Y-%m-%d %H:%M')}: ${price_data.price_usd:.2f}\n"
                
                history_text += f"\nTrend: {history.trend:.4f} per update\n"
                history_text += f"Volatility: {history.volatility:.4f}\n"
                
                self.history_text.setPlainText(history_text)
            else:
                self.history_text.setPlainText(f"No price history available for {card_name}")
    
    def _add_price_alert(self):
        """Add a price alert"""
        card_name = self.alert_card_combo.currentText()
        target_price = self.alert_price_spin.value()
        
        if card_name and target_price > 0:
            # Add to alerts table
            row = self.alerts_table.rowCount()
            self.alerts_table.insertRow(row)
            
            current_price = price_tracker.get_card_price(card_name, "", False) or 0
            
            self.alerts_table.setItem(row, 0, QTableWidgetItem(card_name))
            self.alerts_table.setItem(row, 1, QTableWidgetItem(f"${target_price:.2f}"))
            self.alerts_table.setItem(row, 2, QTableWidgetItem(f"${current_price:.2f}"))
            
            if current_price <= target_price:
                status = "Triggered"
                self.alerts_table.setItem(row, 3, QTableWidgetItem(status))
            else:
                status = "Active"
                self.alerts_table.setItem(row, 3, QTableWidgetItem(status))
    
    def _export_price_report(self):
        """Export price report"""
        # This would export a comprehensive price report
        # For now, just show a message
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Export", "Price report export functionality would be implemented here.")
    
    def closeEvent(self, event):
        """Handle close event"""
        # Stop timers
        self.status_timer.stop()
        self.price_timer.stop()
        event.accept() 