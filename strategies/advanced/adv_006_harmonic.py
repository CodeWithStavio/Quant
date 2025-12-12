"""
ADV_006: Harmonic Pattern Strategy
----------------------------------
Simplified harmonic pattern detection.

Entry Long: Bullish harmonic completion
Entry Short: Bearish harmonic completion

Optimal Timeframes: 1h, 4h
Complexity: 8/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class HarmonicPattern(Strategy):
    """Harmonic Pattern Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_006"
        self.strategy_name = "Harmonic Pattern"
        self.complexity = 8
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'fib_tolerance', 'type': float, 'min': 0.03, 'max': 0.1, 'default': 0.05},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _find_xabcd(self) -> dict:
        """Find potential XABCD harmonic points"""
        lookback = self.hp['lookback']
        swings = []

        for i in range(3, lookback):
            if i + 2 >= len(self.candles):
                continue

            # Swing high
            if (self.candles[-i, 3] > self.candles[-i-1, 3] and
                self.candles[-i, 3] > self.candles[-i+1, 3]):
                swings.append({'type': 'H', 'price': self.candles[-i, 3], 'idx': i})

            # Swing low
            if (self.candles[-i, 4] < self.candles[-i-1, 4] and
                self.candles[-i, 4] < self.candles[-i+1, 4]):
                swings.append({'type': 'L', 'price': self.candles[-i, 4], 'idx': i})

        # Sort by index (most recent first)
        swings = sorted(swings, key=lambda x: x['idx'])[:5]

        if len(swings) >= 4:
            return {
                'X': swings[0] if len(swings) > 0 else None,
                'A': swings[1] if len(swings) > 1 else None,
                'B': swings[2] if len(swings) > 2 else None,
                'C': swings[3] if len(swings) > 3 else None,
                'D': {'price': self.close, 'type': 'current'}
            }
        return {}

    def _check_gartley_bullish(self) -> bool:
        """Check for bullish Gartley pattern"""
        points = self._find_xabcd()
        if not points or 'X' not in points or 'A' not in points:
            return False

        if points['X'] is None or points['A'] is None:
            return False

        tol = self.hp['fib_tolerance']

        # Gartley ratios: AB = 61.8% XA, BC = 38.2-88.6% AB, CD = 127.2-161.8% BC
        xa = abs(points['A']['price'] - points['X']['price'])
        if xa == 0:
            return False

        # Check if X is low and A is high (bullish setup)
        if points['X']['type'] != 'L' or points['A']['type'] != 'H':
            return False

        # D should be near 78.6% XA retracement
        target_d = points['X']['price'] + xa * 0.786
        current_near_target = abs(self.close - target_d) / xa < tol * 2

        # Bullish reversal candle
        bullish = self.close > self.open

        return current_near_target and bullish

    def _check_gartley_bearish(self) -> bool:
        """Check for bearish Gartley pattern"""
        points = self._find_xabcd()
        if not points or 'X' not in points or 'A' not in points:
            return False

        if points['X'] is None or points['A'] is None:
            return False

        tol = self.hp['fib_tolerance']

        xa = abs(points['A']['price'] - points['X']['price'])
        if xa == 0:
            return False

        # Check if X is high and A is low (bearish setup)
        if points['X']['type'] != 'H' or points['A']['type'] != 'L':
            return False

        # D should be near 78.6% XA retracement
        target_d = points['X']['price'] - xa * 0.786
        current_near_target = abs(self.close - target_d) / xa < tol * 2

        # Bearish reversal candle
        bearish = self.close < self.open

        return current_near_target and bearish

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._check_gartley_bullish()

    def should_short(self) -> bool:
        return self._check_gartley_bearish()

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
        rsi = ta.rsi(self.candles, period=14)
        if self.is_long and rsi > 70:
            self.liquidate()
        elif self.is_short and rsi < 30:
            self.liquidate()
