"""
ML_001: Pattern Recognition Strategy
------------------------------------
Statistical pattern recognition using historical price patterns.

Entry Long: Detected bullish pattern match
Entry Short: Detected bearish pattern match

Optimal Timeframes: 1h, 4h
Complexity: 7/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class PatternRecognition(Strategy):
    """Pattern Recognition Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_001"
        self.strategy_name = "Pattern Recognition"
        self.complexity = 7
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'pattern_length', 'type': int, 'min': 5, 'max': 10, 'default': 7},
            {'name': 'lookback', 'type': int, 'min': 50, 'max': 150, 'default': 100},
            {'name': 'similarity_threshold', 'type': float, 'min': 0.7, 'max': 0.9, 'default': 0.8},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _normalize_pattern(self, prices: np.ndarray) -> np.ndarray:
        """Normalize price pattern to 0-1 range"""
        min_p = np.min(prices)
        max_p = np.max(prices)
        if max_p == min_p:
            return np.zeros_like(prices)
        return (prices - min_p) / (max_p - min_p)

    def _calculate_similarity(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """Calculate cosine similarity between patterns"""
        dot = np.dot(p1, p2)
        norm1 = np.linalg.norm(p1)
        norm2 = np.linalg.norm(p2)
        if norm1 == 0 or norm2 == 0:
            return 0
        return dot / (norm1 * norm2)

    def _find_similar_patterns(self, current_pattern: np.ndarray) -> List[dict]:
        """Find similar historical patterns"""
        lookback = self.hp['lookback']
        pattern_len = self.hp['pattern_length']
        closes = self.candles[-lookback:, 2]

        similar_patterns = []
        current_norm = self._normalize_pattern(current_pattern)

        for i in range(len(closes) - pattern_len - 1):
            hist_pattern = closes[i:i + pattern_len]
            hist_norm = self._normalize_pattern(hist_pattern)
            similarity = self._calculate_similarity(current_norm, hist_norm)

            if similarity >= self.hp['similarity_threshold']:
                # What happened after this pattern?
                next_return = (closes[i + pattern_len] - closes[i + pattern_len - 1]) / closes[i + pattern_len - 1]
                similar_patterns.append({
                    'similarity': similarity,
                    'next_return': next_return
                })

        return similar_patterns

    @property
    def current_pattern(self) -> np.ndarray:
        return self.candles[-self.hp['pattern_length']:, 2]

    @property
    def pattern_signal(self) -> float:
        """Calculate expected direction based on similar patterns"""
        patterns = self._find_similar_patterns(self.current_pattern)
        if not patterns:
            return 0

        # Weight by similarity
        total_weight = sum(p['similarity'] for p in patterns)
        if total_weight == 0:
            return 0

        weighted_return = sum(p['similarity'] * p['next_return'] for p in patterns) / total_weight
        return weighted_return

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.pattern_signal > 0.002  # Expected positive return

    def should_short(self) -> bool:
        return self.pattern_signal < -0.002  # Expected negative return

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        pass
