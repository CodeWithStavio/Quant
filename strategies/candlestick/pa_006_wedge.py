"""
PA_006: Wedge Pattern Strategy
------------------------------
Rising wedge (bearish) and falling wedge (bullish) patterns.

Entry Long: Breakout from falling wedge
Entry Short: Breakdown from rising wedge

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict, Tuple


class WedgeStrategy(Strategy):
    """Wedge Pattern Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PA_006"
        self.strategy_name = "Wedge Pattern"
        self.complexity = 6
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 60, 'default': 40},
            {'name': 'convergence_threshold', 'type': float, 'min': 0.3, 'max': 0.8, 'default': 0.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _calculate_regression_line(self, points: List[Tuple[int, float]]) -> Tuple[float, float]:
        """Calculate linear regression line"""
        if len(points) < 2:
            return 0, 0

        x = np.array([p[0] for p in points])
        y = np.array([p[1] for p in points])

        n = len(points)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_xx = np.sum(x * x)

        denom = n * sum_xx - sum_x * sum_x
        if denom == 0:
            return 0, 0

        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

        return slope, intercept

    def _detect_rising_wedge(self) -> dict:
        """Detect rising wedge (bearish pattern)"""
        lookback = self.hp['lookback']
        highs = self.candles[-lookback:, 3]
        lows = self.candles[-lookback:, 4]

        # Find swing points
        swing_highs = []
        swing_lows = []

        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append((i, highs[i]))

            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append((i, lows[i]))

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {'valid': False}

        # Calculate trendlines
        upper_slope, upper_intercept = self._calculate_regression_line(swing_highs)
        lower_slope, lower_intercept = self._calculate_regression_line(swing_lows)

        # Rising wedge: both lines rising, converging
        if upper_slope <= 0 or lower_slope <= 0:
            return {'valid': False}

        # Lines must converge (upper slope < lower slope)
        if upper_slope >= lower_slope:
            return {'valid': False}

        # Calculate current trendline values
        curr_upper = upper_slope * (lookback - 1) + upper_intercept
        curr_lower = lower_slope * (lookback - 1) + lower_intercept

        return {
            'valid': True,
            'upper_line': curr_upper,
            'lower_line': curr_lower,
            'upper_slope': upper_slope,
            'lower_slope': lower_slope
        }

    def _detect_falling_wedge(self) -> dict:
        """Detect falling wedge (bullish pattern)"""
        lookback = self.hp['lookback']
        highs = self.candles[-lookback:, 3]
        lows = self.candles[-lookback:, 4]

        # Find swing points
        swing_highs = []
        swing_lows = []

        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append((i, highs[i]))

            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append((i, lows[i]))

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {'valid': False}

        # Calculate trendlines
        upper_slope, upper_intercept = self._calculate_regression_line(swing_highs)
        lower_slope, lower_intercept = self._calculate_regression_line(swing_lows)

        # Falling wedge: both lines falling, converging
        if upper_slope >= 0 or lower_slope >= 0:
            return {'valid': False}

        # Lines must converge (lower slope < upper slope, i.e., lower falls faster)
        if lower_slope >= upper_slope:
            return {'valid': False}

        # Calculate current trendline values
        curr_upper = upper_slope * (lookback - 1) + upper_intercept
        curr_lower = lower_slope * (lookback - 1) + lower_intercept

        return {
            'valid': True,
            'upper_line': curr_upper,
            'lower_line': curr_lower,
            'upper_slope': upper_slope,
            'lower_slope': lower_slope
        }

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        pattern = self._detect_falling_wedge()
        if not pattern['valid']:
            return False

        # Breakout above upper trendline
        prev_close = self.candles[-2, 2]
        return prev_close < pattern['upper_line'] and self.close > pattern['upper_line']

    def should_short(self) -> bool:
        pattern = self._detect_rising_wedge()
        if not pattern['valid']:
            return False

        # Breakdown below lower trendline
        prev_close = self.candles[-2, 2]
        return prev_close > pattern['lower_line'] and self.close < pattern['lower_line']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        pattern = self._detect_falling_wedge()
        stop = pattern['lower_line'] - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        pattern = self._detect_rising_wedge()
        stop = pattern['upper_line'] + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
