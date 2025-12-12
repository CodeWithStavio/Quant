"""
PA_003: Trendline Strategy
--------------------------
Trade bounces and breaks of dynamically calculated trendlines.

Entry Long: Price bounces off uptrend line
Entry Short: Price bounces off downtrend line

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict, Tuple


class TrendlineStrategy(Strategy):
    """Trendline Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PA_003"
        self.strategy_name = "Trendline"
        self.complexity = 6
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 60, 'default': 40},
            {'name': 'touch_tolerance', 'type': float, 'min': 0.002, 'max': 0.01, 'default': 0.005},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _find_swing_lows(self) -> List[Tuple[int, float]]:
        """Find swing lows with indices"""
        lookback = self.hp['lookback']
        lows = self.candles[-lookback:, 4]
        swing_lows = []

        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append((i, lows[i]))

        return swing_lows

    def _find_swing_highs(self) -> List[Tuple[int, float]]:
        """Find swing highs with indices"""
        lookback = self.hp['lookback']
        highs = self.candles[-lookback:, 3]
        swing_highs = []

        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append((i, highs[i]))

        return swing_highs

    def _calculate_uptrend_line(self) -> Tuple[float, float]:
        """Calculate uptrend line from swing lows"""
        swing_lows = self._find_swing_lows()

        if len(swing_lows) < 2:
            return 0, 0

        # Use two most recent swing lows
        recent_lows = swing_lows[-2:]
        x1, y1 = recent_lows[0]
        x2, y2 = recent_lows[1]

        if x2 == x1:
            return 0, 0

        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1

        return slope, intercept

    def _calculate_downtrend_line(self) -> Tuple[float, float]:
        """Calculate downtrend line from swing highs"""
        swing_highs = self._find_swing_highs()

        if len(swing_highs) < 2:
            return 0, 0

        # Use two most recent swing highs
        recent_highs = swing_highs[-2:]
        x1, y1 = recent_highs[0]
        x2, y2 = recent_highs[1]

        if x2 == x1:
            return 0, 0

        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1

        return slope, intercept

    def _get_uptrend_value(self) -> float:
        """Get current uptrend line value"""
        slope, intercept = self._calculate_uptrend_line()
        lookback = self.hp['lookback']
        return slope * (lookback - 1) + intercept

    def _get_downtrend_value(self) -> float:
        """Get current downtrend line value"""
        slope, intercept = self._calculate_downtrend_line()
        lookback = self.hp['lookback']
        return slope * (lookback - 1) + intercept

    def _at_uptrend_support(self) -> bool:
        """Check if price is at uptrend support"""
        slope, _ = self._calculate_uptrend_line()
        if slope <= 0:  # Must be rising
            return False

        trendline_value = self._get_uptrend_value()
        tolerance = self.close * self.hp['touch_tolerance']

        return abs(self.low - trendline_value) <= tolerance and self.close > self.open

    def _at_downtrend_resistance(self) -> bool:
        """Check if price is at downtrend resistance"""
        slope, _ = self._calculate_downtrend_line()
        if slope >= 0:  # Must be falling
            return False

        trendline_value = self._get_downtrend_value()
        tolerance = self.close * self.hp['touch_tolerance']

        return abs(self.high - trendline_value) <= tolerance and self.close < self.open

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._at_uptrend_support()

    def should_short(self) -> bool:
        return self._at_downtrend_resistance()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        trendline = self._get_uptrend_value()
        stop = min(trendline, self.low) - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        trendline = self._get_downtrend_value()
        stop = max(trendline, self.high) + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
