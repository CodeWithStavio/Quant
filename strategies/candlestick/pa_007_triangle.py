"""
PA_007: Triangle Pattern Strategy
---------------------------------
Ascending, descending, and symmetrical triangles.

Entry Long: Breakout from ascending/symmetrical triangle
Entry Short: Breakdown from descending/symmetrical triangle

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict, Tuple


class TriangleStrategy(Strategy):
    """Triangle Pattern Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PA_007"
        self.strategy_name = "Triangle Pattern"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 60, 'default': 40},
            {'name': 'flat_threshold', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _find_swing_points(self) -> Tuple[List, List]:
        """Find swing highs and lows"""
        lookback = self.hp['lookback']
        highs = self.candles[-lookback:, 3]
        lows = self.candles[-lookback:, 4]

        swing_highs = []
        swing_lows = []

        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append((i, highs[i]))

            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append((i, lows[i]))

        return swing_highs, swing_lows

    def _calculate_slope(self, points: List[Tuple[int, float]]) -> float:
        """Calculate slope of points"""
        if len(points) < 2:
            return 0

        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])

        n = len(points)
        denom = n * np.sum(x * x) - np.sum(x) ** 2
        if denom == 0:
            return 0

        return (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / denom

    def _detect_ascending_triangle(self) -> dict:
        """Detect ascending triangle (bullish)"""
        swing_highs, swing_lows = self._find_swing_points()

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {'valid': False}

        upper_slope = self._calculate_slope(swing_highs)
        lower_slope = self._calculate_slope(swing_lows)

        # Ascending: flat top, rising bottom
        flat_threshold = self.close * self.hp['flat_threshold']
        is_flat_top = abs(upper_slope) < flat_threshold
        is_rising_bottom = lower_slope > flat_threshold

        if not (is_flat_top and is_rising_bottom):
            return {'valid': False}

        # Get resistance level (average of swing highs)
        resistance = np.mean([h[1] for h in swing_highs[-3:]])

        return {
            'valid': True,
            'resistance': resistance,
            'pattern_type': 'ascending'
        }

    def _detect_descending_triangle(self) -> dict:
        """Detect descending triangle (bearish)"""
        swing_highs, swing_lows = self._find_swing_points()

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {'valid': False}

        upper_slope = self._calculate_slope(swing_highs)
        lower_slope = self._calculate_slope(swing_lows)

        # Descending: falling top, flat bottom
        flat_threshold = self.close * self.hp['flat_threshold']
        is_falling_top = upper_slope < -flat_threshold
        is_flat_bottom = abs(lower_slope) < flat_threshold

        if not (is_falling_top and is_flat_bottom):
            return {'valid': False}

        # Get support level (average of swing lows)
        support = np.mean([l[1] for l in swing_lows[-3:]])

        return {
            'valid': True,
            'support': support,
            'pattern_type': 'descending'
        }

    def _detect_symmetrical_triangle(self) -> dict:
        """Detect symmetrical triangle (continuation)"""
        swing_highs, swing_lows = self._find_swing_points()

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {'valid': False}

        upper_slope = self._calculate_slope(swing_highs)
        lower_slope = self._calculate_slope(swing_lows)

        # Symmetrical: falling top, rising bottom (converging)
        flat_threshold = self.close * self.hp['flat_threshold']
        is_falling_top = upper_slope < -flat_threshold
        is_rising_bottom = lower_slope > flat_threshold

        if not (is_falling_top and is_rising_bottom):
            return {'valid': False}

        # Get current trendline values
        lookback = self.hp['lookback']
        upper_val = swing_highs[-1][1] + upper_slope * (lookback - swing_highs[-1][0])
        lower_val = swing_lows[-1][1] + lower_slope * (lookback - swing_lows[-1][0])

        return {
            'valid': True,
            'upper_line': upper_val,
            'lower_line': lower_val,
            'pattern_type': 'symmetrical'
        }

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Ascending triangle breakout
        asc = self._detect_ascending_triangle()
        if asc['valid']:
            prev_close = self.candles[-2, 2]
            if prev_close < asc['resistance'] and self.close > asc['resistance']:
                return True

        # Symmetrical triangle upside breakout
        sym = self._detect_symmetrical_triangle()
        if sym['valid']:
            prev_close = self.candles[-2, 2]
            if prev_close < sym['upper_line'] and self.close > sym['upper_line']:
                return True

        return False

    def should_short(self) -> bool:
        # Descending triangle breakdown
        desc = self._detect_descending_triangle()
        if desc['valid']:
            prev_close = self.candles[-2, 2]
            if prev_close > desc['support'] and self.close < desc['support']:
                return True

        # Symmetrical triangle downside breakdown
        sym = self._detect_symmetrical_triangle()
        if sym['valid']:
            prev_close = self.candles[-2, 2]
            if prev_close > sym['lower_line'] and self.close < sym['lower_line']:
                return True

        return False

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
