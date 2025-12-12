"""
STAT_010: Entropy Analysis Strategy
-----------------------------------
Trade based on price entropy (randomness) levels.

Entry Long: Low entropy regime with bullish bias
Entry Short: Low entropy regime with bearish bias

Optimal Timeframes: 1h, 4h
Complexity: 8/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class EntropyAnalysis(Strategy):
    """Entropy Analysis Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_010"
        self.strategy_name = "Entropy Analysis"
        self.complexity = 8
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 80, 'default': 50},
            {'name': 'bins', 'type': int, 'min': 5, 'max': 15, 'default': 10},
            {'name': 'low_entropy_pct', 'type': float, 'min': 20, 'max': 40, 'default': 30},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_entropy(self) -> float:
        """Calculate Shannon entropy of returns"""
        lookback = self.hp['lookback']
        returns = np.diff(self.candles[-lookback:, 2]) / self.candles[-lookback-1:-1, 2]

        # Discretize returns into bins
        bins = self.hp['bins']
        hist, _ = np.histogram(returns, bins=bins)
        probs = hist / len(returns)
        probs = probs[probs > 0]  # Remove zeros

        # Shannon entropy
        entropy = -np.sum(probs * np.log2(probs))

        # Normalize by max entropy (uniform distribution)
        max_entropy = np.log2(bins)
        return entropy / max_entropy if max_entropy > 0 else 0

    def _get_entropy_percentile(self) -> float:
        """Get entropy percentile over history"""
        lookback = self.hp['lookback']
        current_entropy = self._calculate_entropy()

        entropy_history = []
        for i in range(10, lookback):
            if len(self.candles) > lookback + i:
                returns = np.diff(self.candles[-lookback-i:-i, 2]) / self.candles[-lookback-i-1:-i-1, 2]
                hist, _ = np.histogram(returns, bins=self.hp['bins'])
                probs = hist / len(returns)
                probs = probs[probs > 0]
                if len(probs) > 0:
                    ent = -np.sum(probs * np.log2(probs)) / np.log2(self.hp['bins'])
                    entropy_history.append(ent)

        if not entropy_history:
            return 50

        return np.sum(np.array(entropy_history) < current_entropy) / len(entropy_history) * 100

    @property
    def entropy(self) -> float:
        return self._calculate_entropy()

    @property
    def entropy_percentile(self) -> float:
        return self._get_entropy_percentile()

    @property
    def is_low_entropy(self) -> bool:
        """Low entropy = more predictable patterns"""
        return self.entropy_percentile < self.hp['low_entropy_pct']

    @property
    def trend(self) -> int:
        ma = ta.sma(self.candles, period=20)
        if self.close > ma:
            return 1
        elif self.close < ma:
            return -1
        return 0

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Low entropy (predictable) with bullish trend
        return self.is_low_entropy and self.trend == 1

    def should_short(self) -> bool:
        # Low entropy (predictable) with bearish trend
        return self.is_low_entropy and self.trend == -1

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
        # Exit when entropy increases (becomes unpredictable)
        if self.entropy_percentile > 60:
            self.liquidate()
        # Or on trend reversal
        elif self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()
