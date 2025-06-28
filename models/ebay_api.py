"""
eBay API Integration for FoS_DeckPro
Implements APTPT/REI/HCE-optimized eBay marketplace integration
"""

import os
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

class EbayCondition(Enum):
    """eBay condition codes for MTG cards"""
    NEW = "1000"
    LIKE_NEW = "1500"
    EXCELLENT = "2000"
    VERY_GOOD = "2500"
    GOOD = "3000"
    ACCEPTABLE = "4000"
    FOR_PARTS = "5000"

class EbayPriceType(Enum):
    """eBay price types"""
    FIXED_PRICE = "FIXED_PRICE"
    AUCTION = "AUCTION"
    BEST_OFFER = "BEST_OFFER"

@dataclass
class EbayPriceData:
    """eBay price data structure"""
    card_name: str
    set_code: str
    condition: str
    price_usd: float
    price_usd_foil: Optional[float]
    listing_type: EbayPriceType
    shipping_cost: float
    total_price: float
    confidence: float
    timestamp: datetime
    listing_count: int
    source: str = "ebay"

class EbayAPIIntegration:
    """
    eBay API Integration with APTPT/REI/HCE optimization
    
    Features:
    - APTPT-optimized rate limiting and error recovery
    - REI-balanced price aggregation across conditions
    - HCE-harmonized market convergence
    - Real-time MTG card price fetching
    - Market insights and trend analysis
    """
    
    def __init__(self):
        # API Configuration
        self.api_key = os.getenv('EBAY_API_KEY', '')
        self.base_url = "https://api.ebay.com"
        self.mtg_category_id = "2536"  # Trading Card Games
        
        # APTPT Rate Limiting
        self.rate_limiter = {
            'calls_made': 0,
            'calls_limit': 5000,
            'window_start': time.time(),
            'window_duration': 86400,  # 24 hours
            'min_interval': 0.1  # Minimum time between calls
        }
        
        # REI Balance Parameters
        self.condition_weights = {
            EbayCondition.NEW: 1.0,
            EbayCondition.LIKE_NEW: 0.95,
            EbayCondition.EXCELLENT: 0.9,
            EbayCondition.VERY_GOOD: 0.8,
            EbayCondition.GOOD: 0.7,
            EbayCondition.ACCEPTABLE: 0.5,
            EbayCondition.FOR_PARTS: 0.3
        }
        
        # HCE Harmony Parameters
        self.price_harmony_factor = 0.95
        self.market_convergence_threshold = 0.1
        self.trend_stability_factor = 0.8
        
        # Performance Tracking
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.error_count = 0
        self.last_optimization = time.time()
        
        # Price Cache
        self.price_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Control System
        self.update_thread = None
        self.running = False
        self.update_queue = queue.Queue()
        
    def is_configured(self) -> bool:
        """Check if eBay API is properly configured"""
        return bool(self.api_key and self.api_key.strip())
    
    def start_price_tracking(self):
        """Start eBay price tracking system"""
        if not self.is_configured():
            print("⚠️ eBay API not configured - skipping price tracking")
            return
            
        if self.update_thread is None or not self.update_thread.is_alive():
            self.running = True
            self.update_thread = threading.Thread(target=self._price_update_loop, daemon=True)
            self.update_thread.start()
            
            # Optimize for eBay price tracking operation
            if UNIFIED_SYSTEM_AVAILABLE:
                unified_manager.optimize_for_operation("ebay_price_tracking")
    
    def stop_price_tracking(self):
        """Stop eBay price tracking system"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def _price_update_loop(self):
        """Main eBay price update loop with APTPT optimization"""
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
                self._optimize_condition_balance()
                
                # Apply HCE harmony optimization
                self._optimize_price_harmony()
                
                # Log performance metrics
                self._log_performance_metrics()
                
                time.sleep(60)  # 1 minute update interval
                
            except Exception as e:
                self._log_error(f"eBay price update error: {e}")
                time.sleep(10)  # Wait before retrying
    
    def _calculate_optimal_batch_size(self) -> int:
        """Calculate optimal batch size using APTPT principles"""
        # Base batch size
        base_size = 20
        
        # Adjust based on rate limit status
        remaining_calls = self.rate_limiter['calls_limit'] - self.rate_limiter['calls_made']
        if remaining_calls < 100:
            return 5  # Conservative batch size
        elif remaining_calls < 500:
            return 10  # Moderate batch size
        else:
            return base_size  # Full batch size
    
    def _get_cards_needing_updates(self) -> List[Tuple[str, str]]:
        """Get cards that need eBay price updates"""
        current_time = time.time()
        cards_needing_updates = []
        
        for card_key, price_data in self.price_cache.items():
            if current_time - price_data.timestamp.timestamp() > self.cache_ttl:
                # Parse card key (format: "card_name|set_code")
                card_name, set_code = card_key.split("|", 1)
                cards_needing_updates.append((card_name, set_code))
        
        return cards_needing_updates
    
    async def _update_prices_batch(self, cards: List[Tuple[str, str]]):
        """Update eBay prices for a batch of cards"""
        async with aiohttp.ClientSession() as session:
            # Create tasks for concurrent price updates
            tasks = []
            for card_name, set_code in cards:
                task = self._update_card_price(session, card_name, set_code)
                tasks.append(task)
            
            # Execute tasks with concurrency limit
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
            async def limited_task(task):
                async with semaphore:
                    return await task
            
            limited_tasks = [limited_task(task) for task in tasks]
            results = await asyncio.gather(*limited_tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    self._log_error(f"eBay price update failed: {result}")
    
    async def _update_card_price(self, session: aiohttp.ClientSession, card_name: str, set_code: str):
        """Update eBay price for a single card"""
        try:
            # Apply APTPT rate limiting
            await self._wait_for_rate_limit()
            
            # Search eBay for MTG cards
            search_results = await self._search_ebay_mtg(session, card_name, set_code)
            
            if search_results:
                # Apply REI balance for price aggregation
                price_data = self._apply_rei_balance(card_name, set_code, search_results)
                
                # Apply HCE harmony for price stability
                stable_price_data = self._apply_hce_harmony(card_name, set_code, price_data)
                
                # Cache the result
                card_key = f"{card_name}|{set_code}"
                self.price_cache[card_key] = stable_price_data
                
                self.request_count += 1
                
        except Exception as e:
            self._log_error(f"eBay price update failed for {card_name}: {e}")
            self.error_count += 1
    
    async def _wait_for_rate_limit(self):
        """Wait for rate limit using APTPT principles"""
        current_time = time.time()
        
        # Check if we need to reset the window
        if current_time - self.rate_limiter['window_start'] > self.rate_limiter['window_duration']:
            self.rate_limiter['calls_made'] = 0
            self.rate_limiter['window_start'] = current_time
        
        # Check if we're at the limit
        if self.rate_limiter['calls_made'] >= self.rate_limiter['calls_limit']:
            wait_time = self.rate_limiter['window_duration'] - (current_time - self.rate_limiter['window_start'])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                self.rate_limiter['calls_made'] = 0
                self.rate_limiter['window_start'] = time.time()
        
        # Apply minimum interval
        await asyncio.sleep(self.rate_limiter['min_interval'])
        self.rate_limiter['calls_made'] += 1
    
    async def _search_ebay_mtg(self, session: aiohttp.ClientSession, card_name: str, set_code: str) -> List[Dict]:
        """Search eBay for MTG cards with proper filtering"""
        search_query = f"{card_name} {set_code} magic the gathering"
        
        # Build filter string for MTG cards
        condition_filter = "|".join([cond.value for cond in EbayCondition])
        
        params = {
            'q': search_query,
            'filter': f'categoryIds:{self.mtg_category_id},conditions:{{{condition_filter}}}',
            'sort': 'price',
            'limit': 50,
            'fieldgroups': 'ASPECT_REFINEMENTS,SHIPPING_INFO'
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY-US'
        }
        
        try:
            async with session.get(
                f"{self.base_url}/buy/browse/v1/item_summary/search",
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('itemSummaries', [])
                else:
                    self._log_error(f"eBay API error: {response.status} - {await response.text()}")
                    return []
        except Exception as e:
            self._log_error(f"eBay search failed: {e}")
            return []
    
    def _apply_rei_balance(self, card_name: str, set_code: str, search_results: List[Dict]) -> EbayPriceData:
        """Apply REI balance for price aggregation across conditions"""
        if not search_results:
            return self._create_default_price_data(card_name, set_code)
        
        # Group by condition and calculate weighted averages
        condition_prices = {}
        condition_counts = {}
        
        for item in search_results:
            condition = item.get('condition', 'UNKNOWN')
            price = float(item.get('price', {}).get('value', 0))
            shipping = float(item.get('shippingOptions', [{}])[0].get('shippingCost', {}).get('value', 0))
            total_price = price + shipping
            
            if condition not in condition_prices:
                condition_prices[condition] = []
                condition_counts[condition] = 0
            
            condition_prices[condition].append(total_price)
            condition_counts[condition] += 1
        
        # Calculate weighted average prices
        weighted_prices = {}
        for condition, prices in condition_prices.items():
            if prices:
                avg_price = sum(prices) / len(prices)
                weight = self.condition_weights.get(EbayCondition(condition), 0.5)
                weighted_prices[condition] = avg_price * weight
        
        # Find the most common condition for base price
        most_common_condition = max(condition_counts.items(), key=lambda x: x[1])[0]
        base_price = weighted_prices.get(most_common_condition, 0)
        
        # Calculate foil price (if available)
        foil_price = self._extract_foil_price(search_results)
        
        return EbayPriceData(
            card_name=card_name,
            set_code=set_code,
            condition=most_common_condition,
            price_usd=base_price,
            price_usd_foil=foil_price,
            listing_type=EbayPriceType.FIXED_PRICE,
            shipping_cost=0,  # Already included in price
            total_price=base_price,
            confidence=0.85,
            timestamp=datetime.utcnow(),
            listing_count=len(search_results)
        )
    
    def _extract_foil_price(self, search_results: List[Dict]) -> Optional[float]:
        """Extract foil price from search results"""
        foil_items = []
        
        for item in search_results:
            title = item.get('title', '').lower()
            if 'foil' in title or 'etched' in title:
                price = float(item.get('price', {}).get('value', 0))
                shipping = float(item.get('shippingOptions', [{}])[0].get('shippingCost', {}).get('value', 0))
                foil_items.append(price + shipping)
        
        if foil_items:
            return sum(foil_items) / len(foil_items)
        return None
    
    def _apply_hce_harmony(self, card_name: str, set_code: str, price_data: EbayPriceData) -> EbayPriceData:
        """Apply HCE harmony for price stability"""
        card_key = f"{card_name}|{set_code}"
        
        # Check if we have historical data
        if card_key in self.price_cache:
            historical_data = self.price_cache[card_key]
            
            # Calculate price trend
            price_change = abs(price_data.price_usd - historical_data.price_usd) / historical_data.price_usd
            
            # Apply HCE harmony factor if price change is significant
            if price_change > self.market_convergence_threshold:
                # Apply harmony factor to stabilize price
                adjusted_price = price_data.price_usd * self.price_harmony_factor
                price_data.price_usd = adjusted_price
                price_data.total_price = adjusted_price
        
        return price_data
    
    def _create_default_price_data(self, card_name: str, set_code: str) -> EbayPriceData:
        """Create default price data when no eBay results found"""
        return EbayPriceData(
            card_name=card_name,
            set_code=set_code,
            condition="UNKNOWN",
            price_usd=0.0,
            price_usd_foil=None,
            listing_type=EbayPriceType.FIXED_PRICE,
            shipping_cost=0.0,
            total_price=0.0,
            confidence=0.0,
            timestamp=datetime.utcnow(),
            listing_count=0
        )
    
    def _optimize_condition_balance(self):
        """Optimize condition balance using REI principles"""
        # This would adjust condition weights based on market availability
        # For now, maintain current weights
        pass
    
    def _optimize_price_harmony(self):
        """Optimize price harmony using HCE principles"""
        # This would adjust harmony parameters based on market conditions
        # For now, maintain current parameters
        pass
    
    def get_card_price(self, card_name: str, set_code: str, foil: bool = False) -> Optional[float]:
        """Get current eBay price for a card"""
        if not self.is_configured():
            return None
            
        card_key = f"{card_name}|{set_code}"
        
        if card_key in self.price_cache:
            self.cache_hits += 1
            price_data = self.price_cache[card_key]
            
            if foil and price_data.price_usd_foil:
                return price_data.price_usd_foil
            else:
                return price_data.price_usd
        else:
            self.cache_misses += 1
            return None
    
    def get_market_insights(self, card_name: str, set_code: str) -> Dict[str, Any]:
        """Get eBay market insights for a card"""
        if not self.is_configured():
            return {}
            
        card_key = f"{card_name}|{set_code}"
        
        if card_key in self.price_cache:
            price_data = self.price_cache[card_key]
            
            return {
                'listing_count': price_data.listing_count,
                'condition_distribution': self._get_condition_distribution(card_key),
                'price_range': self._get_price_range(card_key),
                'market_confidence': price_data.confidence,
                'last_updated': price_data.timestamp.isoformat()
            }
        
        return {}
    
    def _get_condition_distribution(self, card_key: str) -> Dict[str, int]:
        """Get condition distribution for a card (placeholder)"""
        # This would analyze the actual search results
        return {
            'near_mint': 0,
            'lightly_played': 0,
            'moderately_played': 0,
            'heavily_played': 0
        }
    
    def _get_price_range(self, card_key: str) -> Dict[str, float]:
        """Get price range for a card (placeholder)"""
        # This would analyze the actual search results
        return {
            'min': 0.0,
            'max': 0.0,
            'median': 0.0
        }
    
    def _log_performance_metrics(self):
        """Log performance metrics"""
        cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": "ebay_api",
            "cache_hit_rate": cache_hit_rate,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "cache_size": len(self.price_cache),
            "rate_limit_remaining": self.rate_limiter['calls_limit'] - self.rate_limiter['calls_made']
        }
        
        # Log to APTPT error log if available
        try:
            with open("aptpt_error_log.jsonl", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
    
    def _log_error(self, message: str):
        """Log error message"""
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": "ebay_api",
            "error": message,
            "level": "error"
        }
        
        # Log to APTPT error log if available
        try:
            with open("aptpt_error_log.jsonl", "a") as f:
                f.write(json.dumps(error_entry) + "\n")
        except Exception:
            pass

# Global eBay API instance
ebay_api = EbayAPIIntegration() 