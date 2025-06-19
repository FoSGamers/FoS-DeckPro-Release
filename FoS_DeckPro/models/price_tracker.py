"""
Real-time Price Tracker for FoS_DeckPro
Integrates with multiple pricing sources and uses APTPT/REI/HCE for optimal performance
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import hashlib

# Import unified system for optimization
try:
    from aptpt_pyside6_kit.unified_system_manager import unified_manager
    UNIFIED_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_SYSTEM_AVAILABLE = False

class PriceSource(Enum):
    """Available price sources"""
    SCRYFALL = "scryfall"
    TCGPLAYER = "tcgplayer"
    CARDMARKET = "cardmarket"
    MTGGOLDFISH = "mtggoldfish"

@dataclass
class PriceData:
    """Price data structure"""
    card_name: str
    set_code: str
    price_usd: float
    price_usd_foil: Optional[float]
    price_usd_etched: Optional[float]
    price_eur: Optional[float]
    price_eur_foil: Optional[float]
    source: PriceSource
    timestamp: datetime
    confidence: float  # 0-1 confidence in the price data

@dataclass
class PriceHistory:
    """Price history for a card"""
    card_name: str
    set_code: str
    prices: List[PriceData]
    trend: float  # Price trend over time
    volatility: float  # Price volatility

class PriceTracker:
    """
    Real-time price tracker with APTPT/REI/HCE optimization
    
    Features:
    - Multi-source price aggregation
    - Real-time price updates
    - Price history tracking
    - Market trend analysis
    - APTPT-optimized caching
    - REI-balanced data sources
    - HCE-harmonized price convergence
    """
    
    def __init__(self):
        self.price_cache = {}  # Card -> PriceData
        self.price_history = {}  # Card -> PriceHistory
        self.source_weights = {
            PriceSource.SCRYFALL: 0.4,
            PriceSource.TCGPLAYER: 0.3,
            PriceSource.CARDMARKET: 0.2,
            PriceSource.MTGGOLDFISH: 0.1
        }
        
        # APTPT optimization parameters
        self.cache_ttl = 300  # 5 minutes
        self.update_interval = 60  # 1 minute
        self.max_concurrent_requests = 10
        
        # REI balance parameters
        self.source_balance_threshold = 0.1
        self.price_convergence_threshold = 0.05
        
        # HCE harmony parameters
        self.price_harmony_factor = 0.95
        self.trend_stability_threshold = 0.8
        
        # Control system
        self.update_thread = None
        self.running = False
        self.update_queue = queue.Queue()
        
        # Performance tracking
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_optimization = time.time()
        
    def start_price_tracking(self):
        """Start the price tracking system"""
        if self.update_thread is None or not self.update_thread.is_alive():
            self.running = True
            self.update_thread = threading.Thread(target=self._price_update_loop, daemon=True)
            self.update_thread.start()
            
            # Optimize for price tracking operation
            if UNIFIED_SYSTEM_AVAILABLE:
                unified_manager.optimize_for_operation("price_tracking")
    
    def stop_price_tracking(self):
        """Stop the price tracking system"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def _price_update_loop(self):
        """Main price update loop with APTPT optimization"""
        while self.running:
            try:
                # Get cards that need price updates
                cards_to_update = self._get_cards_needing_updates()
                
                # Apply APTPT optimization for batch size
                optimal_batch_size = self._calculate_optimal_batch_size()
                batch = cards_to_update[:optimal_batch_size]
                
                # Update prices for the batch
                asyncio.run(self._update_prices_batch(batch))
                
                # Apply REI balance optimization
                self._optimize_source_balance()
                
                # Apply HCE harmony optimization
                self._optimize_price_harmony()
                
                # Log performance metrics
                self._log_performance_metrics()
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self._log_error(f"Price update error: {e}")
                time.sleep(10)  # Wait before retrying
    
    def _calculate_optimal_batch_size(self) -> int:
        """Calculate optimal batch size using APTPT principles"""
        # Base batch size
        base_size = 50
        
        # Adjust based on system performance
        if UNIFIED_SYSTEM_AVAILABLE:
            status = unified_manager.get_unified_status()
            performance_index = status.get('performance_index', 0.8)
            
            # Scale batch size based on performance
            if performance_index > 0.9:
                return int(base_size * 1.5)  # Increase batch size
            elif performance_index < 0.7:
                return int(base_size * 0.5)  # Decrease batch size
        
        return base_size
    
    def _get_cards_needing_updates(self) -> List[Tuple[str, str]]:
        """Get cards that need price updates"""
        current_time = time.time()
        cards_needing_updates = []
        
        for card_key, price_data in self.price_cache.items():
            if current_time - price_data.timestamp.timestamp() > self.cache_ttl:
                # Parse card key (format: "card_name|set_code")
                card_name, set_code = card_key.split("|", 1)
                cards_needing_updates.append((card_name, set_code))
        
        return cards_needing_updates
    
    async def _update_prices_batch(self, cards: List[Tuple[str, str]]):
        """Update prices for a batch of cards"""
        async with aiohttp.ClientSession() as session:
            # Create tasks for concurrent price updates
            tasks = []
            for card_name, set_code in cards:
                task = self._update_card_price(session, card_name, set_code)
                tasks.append(task)
            
            # Execute tasks with concurrency limit
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            async def limited_task(task):
                async with semaphore:
                    return await task
            
            limited_tasks = [limited_task(task) for task in tasks]
            results = await asyncio.gather(*limited_tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    self._log_error(f"Price update failed: {result}")
    
    async def _update_card_price(self, session: aiohttp.ClientSession, card_name: str, set_code: str):
        """Update price for a single card"""
        try:
            # Get price from Scryfall (primary source)
            scryfall_price = await self._get_scryfall_price(session, card_name, set_code)
            
            # Get price from TCGPlayer (secondary source)
            tcgplayer_price = await self._get_tcgplayer_price(session, card_name, set_code)
            
            # Apply REI balance to combine prices
            combined_price = self._combine_prices_rei([scryfall_price, tcgplayer_price])
            
            # Apply HCE harmony for price stability
            harmonized_price = self._apply_hce_harmony(card_name, set_code, combined_price)
            
            # Update cache
            card_key = f"{card_name}|{set_code}"
            self.price_cache[card_key] = harmonized_price
            
            # Update price history
            self._update_price_history(card_name, set_code, harmonized_price)
            
            self.request_count += 1
            
        except Exception as e:
            self._log_error(f"Failed to update price for {card_name} ({set_code}): {e}")
    
    async def _get_scryfall_price(self, session: aiohttp.ClientSession, card_name: str, set_code: str) -> Optional[PriceData]:
        """Get price from Scryfall API"""
        try:
            # Use existing Scryfall integration
            from models.scryfall_api import fetch_scryfall_data
            
            # Search for the card
            search_query = f'name:"{card_name}" set:{set_code}'
            card_data = await fetch_scryfall_data(search_query)
            
            if card_data and len(card_data) > 0:
                card = card_data[0]
                return PriceData(
                    card_name=card_name,
                    set_code=set_code,
                    price_usd=float(card.get('usd', 0)) if card.get('usd') else 0,
                    price_usd_foil=float(card.get('usd_foil', 0)) if card.get('usd_foil') else None,
                    price_usd_etched=float(card.get('usd_etched', 0)) if card.get('usd_etched') else None,
                    price_eur=float(card.get('eur', 0)) if card.get('eur') else None,
                    price_eur_foil=float(card.get('eur_foil', 0)) if card.get('eur_foil') else None,
                    source=PriceSource.SCRYFALL,
                    timestamp=datetime.utcnow(),
                    confidence=0.9
                )
        except Exception as e:
            self._log_error(f"Scryfall price fetch failed: {e}")
        
        return None
    
    async def _get_tcgplayer_price(self, session: aiohttp.ClientSession, card_name: str, set_code: str) -> Optional[PriceData]:
        """Get price from TCGPlayer API (simulated)"""
        # This would integrate with TCGPlayer API
        # For now, return None to indicate no TCGPlayer data
        return None
    
    def _combine_prices_rei(self, prices: List[Optional[PriceData]]) -> PriceData:
        """Combine prices using REI principles for universal proportionality"""
        valid_prices = [p for p in prices if p is not None]
        
        if not valid_prices:
            # Return default price data
            return PriceData(
                card_name="",
                set_code="",
                price_usd=0.0,
                price_usd_foil=None,
                price_usd_etched=None,
                price_eur=None,
                price_eur_foil=None,
                source=PriceSource.SCRYFALL,
                timestamp=datetime.utcnow(),
                confidence=0.0
            )
        
        if len(valid_prices) == 1:
            return valid_prices[0]
        
        # Apply REI balance: weighted average based on source confidence
        total_weight = sum(p.confidence for p in valid_prices)
        if total_weight == 0:
            return valid_prices[0]
        
        # Calculate weighted average
        combined_price = PriceData(
            card_name=valid_prices[0].card_name,
            set_code=valid_prices[0].set_code,
            price_usd=sum(p.price_usd * p.confidence for p in valid_prices) / total_weight,
            price_usd_foil=self._combine_optional_prices([p.price_usd_foil for p in valid_prices], [p.confidence for p in valid_prices]),
            price_usd_etched=self._combine_optional_prices([p.price_usd_etched for p in valid_prices], [p.confidence for p in valid_prices]),
            price_eur=self._combine_optional_prices([p.price_eur for p in valid_prices], [p.confidence for p in valid_prices]),
            price_eur_foil=self._combine_optional_prices([p.price_eur_foil for p in valid_prices], [p.confidence for p in valid_prices]),
            source=PriceSource.SCRYFALL,  # Use primary source
            timestamp=datetime.utcnow(),
            confidence=sum(p.confidence for p in valid_prices) / len(valid_prices)
        )
        
        return combined_price
    
    def _combine_optional_prices(self, prices: List[Optional[float]], weights: List[float]) -> Optional[float]:
        """Combine optional prices with weights"""
        valid_prices = [(p, w) for p, w in zip(prices, weights) if p is not None]
        
        if not valid_prices:
            return None
        
        total_weight = sum(w for _, w in valid_prices)
        if total_weight == 0:
            return valid_prices[0][0]
        
        return sum(p * w for p, w in valid_prices) / total_weight
    
    def _apply_hce_harmony(self, card_name: str, set_code: str, price_data: PriceData) -> PriceData:
        """Apply HCE harmony for price stability"""
        card_key = f"{card_name}|{set_code}"
        
        if card_key in self.price_history:
            history = self.price_history[card_key]
            
            # Calculate price trend
            if len(history.prices) > 1:
                recent_prices = history.prices[-5:]  # Last 5 prices
                if len(recent_prices) > 1:
                    # Calculate trend
                    price_values = [p.price_usd for p in recent_prices]
                    trend = (price_values[-1] - price_values[0]) / len(price_values)
                    
                    # Apply HCE harmony factor
                    if abs(trend) < self.trend_stability_threshold:
                        # Price is stable, maintain current price
                        return price_data
                    else:
                        # Price is trending, apply harmony factor
                        adjusted_price = price_data.price_usd * self.price_harmony_factor
                        price_data.price_usd = adjusted_price
        
        return price_data
    
    def _update_price_history(self, card_name: str, set_code: str, price_data: PriceData):
        """Update price history for a card"""
        card_key = f"{card_name}|{set_code}"
        
        if card_key not in self.price_history:
            self.price_history[card_key] = PriceHistory(
                card_name=card_name,
                set_code=set_code,
                prices=[],
                trend=0.0,
                volatility=0.0
            )
        
        history = self.price_history[card_key]
        history.prices.append(price_data)
        
        # Keep only last 100 prices
        if len(history.prices) > 100:
            history.prices = history.prices[-100:]
        
        # Calculate trend and volatility
        if len(history.prices) > 1:
            prices = [p.price_usd for p in history.prices]
            history.trend = (prices[-1] - prices[0]) / len(prices)
            
            # Calculate volatility (standard deviation)
            mean_price = sum(prices) / len(prices)
            variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
            history.volatility = variance ** 0.5
    
    def _optimize_source_balance(self):
        """Optimize source balance using REI principles"""
        # This would adjust source weights based on reliability and availability
        # For now, maintain current weights
        pass
    
    def _optimize_price_harmony(self):
        """Optimize price harmony using HCE principles"""
        # This would adjust harmony parameters based on market conditions
        # For now, maintain current parameters
        pass
    
    def get_card_price(self, card_name: str, set_code: str, foil: bool = False) -> Optional[float]:
        """Get current price for a card"""
        card_key = f"{card_name}|{set_code}"
        
        if card_key in self.price_cache:
            self.cache_hits += 1
            price_data = self.price_cache[card_key]
            
            if foil:
                return price_data.price_usd_foil or price_data.price_usd
            else:
                return price_data.price_usd
        else:
            self.cache_misses += 1
            return None
    
    def get_price_history(self, card_name: str, set_code: str) -> Optional[PriceHistory]:
        """Get price history for a card"""
        card_key = f"{card_name}|{set_code}"
        return self.price_history.get(card_key)
    
    def get_collection_value(self, cards: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate total value of a collection"""
        total_value = 0.0
        foil_value = 0.0
        non_foil_value = 0.0
        
        for card in cards:
            card_name = card.get('Name', '')
            set_code = card.get('Set code', '')
            foil = card.get('Foil', 'normal') == 'foil'
            quantity = int(card.get('Quantity', 1))
            
            price = self.get_card_price(card_name, set_code, foil)
            if price:
                card_value = price * quantity
                total_value += card_value
                
                if foil:
                    foil_value += card_value
                else:
                    non_foil_value += card_value
        
        return {
            'total': total_value,
            'foil': foil_value,
            'non_foil': non_foil_value
        }
    
    def _log_performance_metrics(self):
        """Log performance metrics"""
        cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": "price_tracker",
            "cache_hit_rate": cache_hit_rate,
            "request_count": self.request_count,
            "cache_size": len(self.price_cache),
            "history_size": len(self.price_history)
        }
        
        with open("aptpt_error_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _log_error(self, message: str):
        """Log error messages"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": message,
            "system": "price_tracker"
        }
        with open("aptpt_error_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

# Global price tracker instance
price_tracker = PriceTracker() 