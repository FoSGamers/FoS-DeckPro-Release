from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

class BudgetManager:
    def __init__(self):
        self.budgets: Dict[str, float] = {}
        self.history: Dict[str, List[Dict[str, Any]]] = {}
        self.alerts: Dict[str, List[Dict[str, Any]]] = {}
        
    def set_budget(self, format_name: str, amount: float):
        """Set budget for a format"""
        self.budgets[format_name] = amount
        self._record_budget_change(format_name, amount)
        
    def _record_budget_change(self, format_name: str, amount: float):
        """Record budget change in history"""
        if format_name not in self.history:
            self.history[format_name] = []
            
        self.history[format_name].append({
            'amount': amount,
            'timestamp': datetime.now().isoformat(),
            'reason': 'manual_update'
        })
        
    def check_budget(self, deck: Dict[str, Any], format_name: str) -> Dict[str, Any]:
        """Check if deck is within budget"""
        if format_name not in self.budgets:
            return {'valid': False, 'error': f"No budget set for {format_name}"}
            
        total_cost = sum(card['purchase_price'] * count 
                        for card, count in deck['mainboard'])
        budget = self.budgets[format_name]
        
        result = {
            'valid': total_cost <= budget,
            'total_cost': total_cost,
            'budget': budget,
            'remaining': budget - total_cost
        }
        
        if not result['valid']:
            self._record_alert(format_name, result)
            
        return result
        
    def _record_alert(self, format_name: str, budget_info: Dict[str, Any]):
        """Record budget alert"""
        if format_name not in self.alerts:
            self.alerts[format_name] = []
            
        self.alerts[format_name].append({
            'timestamp': datetime.now().isoformat(),
            'budget_info': budget_info
        })
        
    def get_budget_history(self, format_name: str) -> List[Dict[str, Any]]:
        """Get budget history for a format"""
        return self.history.get(format_name, [])
        
    def get_budget_alerts(self, format_name: str) -> List[Dict[str, Any]]:
        """Get budget alerts for a format"""
        return self.alerts.get(format_name, []) 