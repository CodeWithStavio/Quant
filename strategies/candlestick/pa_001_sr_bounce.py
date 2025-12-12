"""
PA_001: Support/Resistance Bounce Strategy
------------------------------------------
Trade bounces off key support and resistance levels.

Entry Long: Price bounces off support
Entry Short: Price bounces off resistance

Optimal Timeframes: 15m, 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SRBounce(Strategy):
    """Support/Resistance Bounce Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PA_001"
        self.strategy_name = "SR Bounce"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'sr_lookback', 'type': int, 'min': 20, 'max': 100, 'default': 50},
            {'name': 'sr_tolerance', 'type': float, 'min': 0.002, 'max': 0.01, 'default': 0.005},
            {'name': 'bounce_strength', 'type': float, 'min': 0.3, 'max': 0.7, 'default': 0.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _find_support_levels(self) -> List[float]:
        """Find recent support levels"""
        lookback = self.hp['sr_lookback']
        lows = self.candles[-lookback:, 4]
        support_levels = []

        # Find swing lows
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                support_levels.append(lows[i])

        return support_levels

    def _find_resistance_levels(self) -> List[float]:
        """Find recent resistance levels"""
        lookback = self.hp['sr_lookback']
        highs = self.candles[-lookback:, 3]
        resistance_levels = []

        # Find swing highs
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                resistance_levels.append(highs[i])

        return resistance_levels

    def _near_support(self) -> bool:
        """Check if price is near a support level"""
        support_levels = self._find_support_levels()
        tolerance = self.close * self.hp['sr_tolerance']

        for level in support_levels:
            if abs(self.low - level) <= tolerance:
                return True
        return False

    def _near_resistance(self) -> bool:
        """Check if price is near a resistance level"""
        resistance_levels = self._find_resistance_levels()
        tolerance = self.close * self.hp['sr_tolerance']

        for level in resistance_levels:
            if abs(self.high - level) <= tolerance:
                return True
        return False

    def _is_bounce_up(self) -> bool:
        """Check for bullish bounce candle"""
        body = self.close - self.open
        total_range = self.high - self.low

        if total_range == 0:
            return False

        # Bullish candle with lower wick
        lower_wick = min(self.open, self.close) - self.low
        return self.close > self.open and lower_wick / total_range >= self.hp['bounce_strength']

    def _is_bounce_down(self) -> bool:
        """Check for bearish bounce candle"""
        body = self.open - self.close
        total_range = self.high - self.low

        if total_range == 0:
            return False

        # Bearish candle with upper wick
        upper_wick = self.high - max(self.open, self.close)
        return self.close < self.open and upper_wick / total_range >= self.hp['bounce_strength']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._near_support() and self._is_bounce_up()

    def should_short(self) -> bool:
        return self._near_resistance() and self._is_bounce_down()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.low - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = self.high + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
