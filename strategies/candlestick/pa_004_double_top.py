"""
PA_004: Double Top/Bottom Strategy
----------------------------------
Classic reversal patterns with two equal highs/lows.

Entry Long: Neckline breakout after double bottom
Entry Short: Neckline breakout after double top

Optimal Timeframes: 1h, 4h, 1d
Complexity: 6/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DoubleTopBottom(Strategy):
    """Double Top/Bottom Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PA_004"
        self.strategy_name = "Double Top Bottom"
        self.complexity = 6
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 80, 'default': 50},
            {'name': 'peak_tolerance', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'min_retracement', 'type': float, 'min': 0.3, 'max': 0.6, 'default': 0.4},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.5, 'default': 3.5},
        ]

    def _detect_double_top(self) -> dict:
        """Detect double top pattern"""
        lookback = self.hp['lookback']
        highs = self.candles[-lookback:, 3]
        lows = self.candles[-lookback:, 4]

        # Find two highest swing highs
        swing_highs = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append((i, highs[i]))

        if len(swing_highs) < 2:
            return {'valid': False}

        # Check for two approximately equal peaks
        sorted_highs = sorted(swing_highs, key=lambda x: x[1], reverse=True)
        peak1 = sorted_highs[0]
        peak2 = sorted_highs[1]

        tolerance = peak1[1] * self.hp['peak_tolerance']
        if abs(peak1[1] - peak2[1]) > tolerance:
            return {'valid': False}

        # Find neckline (lowest point between peaks)
        start_idx = min(peak1[0], peak2[0])
        end_idx = max(peak1[0], peak2[0])
        neckline = np.min(lows[start_idx:end_idx+1])

        # Check retracement
        pattern_height = ((peak1[1] + peak2[1]) / 2) - neckline
        retracement = pattern_height * self.hp['min_retracement']
        if pattern_height < retracement:
            return {'valid': False}

        return {
            'valid': True,
            'neckline': neckline,
            'peak': (peak1[1] + peak2[1]) / 2,
            'height': pattern_height
        }

    def _detect_double_bottom(self) -> dict:
        """Detect double bottom pattern"""
        lookback = self.hp['lookback']
        highs = self.candles[-lookback:, 3]
        lows = self.candles[-lookback:, 4]

        # Find two lowest swing lows
        swing_lows = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append((i, lows[i]))

        if len(swing_lows) < 2:
            return {'valid': False}

        # Check for two approximately equal troughs
        sorted_lows = sorted(swing_lows, key=lambda x: x[1])
        trough1 = sorted_lows[0]
        trough2 = sorted_lows[1]

        tolerance = trough1[1] * self.hp['peak_tolerance']
        if abs(trough1[1] - trough2[1]) > tolerance:
            return {'valid': False}

        # Find neckline (highest point between troughs)
        start_idx = min(trough1[0], trough2[0])
        end_idx = max(trough1[0], trough2[0])
        neckline = np.max(highs[start_idx:end_idx+1])

        # Check pattern height
        pattern_height = neckline - ((trough1[1] + trough2[1]) / 2)
        retracement = pattern_height * self.hp['min_retracement']
        if pattern_height < retracement:
            return {'valid': False}

        return {
            'valid': True,
            'neckline': neckline,
            'trough': (trough1[1] + trough2[1]) / 2,
            'height': pattern_height
        }

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        pattern = self._detect_double_bottom()
        if not pattern['valid']:
            return False

        # Breakout above neckline
        prev_close = self.candles[-2, 2]
        return prev_close < pattern['neckline'] and self.close > pattern['neckline']

    def should_short(self) -> bool:
        pattern = self._detect_double_top()
        if not pattern['valid']:
            return False

        # Breakdown below neckline
        prev_close = self.candles[-2, 2]
        return prev_close > pattern['neckline'] and self.close < pattern['neckline']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        pattern = self._detect_double_bottom()
        stop = pattern['trough'] - (self.atr * 0.5)
        target = entry + pattern['height']  # Measure move target
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        pattern = self._detect_double_top()
        stop = pattern['peak'] + (self.atr * 0.5)
        target = entry - pattern['height']  # Measure move target
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
