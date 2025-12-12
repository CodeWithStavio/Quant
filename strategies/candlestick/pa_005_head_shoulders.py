"""
PA_005: Head and Shoulders Strategy
-----------------------------------
Classic reversal pattern with head and two shoulders.

Entry Long: Neckline breakout after inverse H&S
Entry Short: Neckline breakdown after H&S

Optimal Timeframes: 4h, 1d
Complexity: 7/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class HeadAndShoulders(Strategy):
    """Head and Shoulders Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PA_005"
        self.strategy_name = "Head Shoulders"
        self.complexity = 7
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 40, 'max': 100, 'default': 60},
            {'name': 'shoulder_tolerance', 'type': float, 'min': 0.02, 'max': 0.05, 'default': 0.03},
            {'name': 'head_ratio_min', 'type': float, 'min': 1.1, 'max': 1.5, 'default': 1.2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _detect_head_shoulders(self) -> dict:
        """Detect head and shoulders (bearish) pattern"""
        lookback = self.hp['lookback']
        highs = self.candles[-lookback:, 3]
        lows = self.candles[-lookback:, 4]

        # Find swing highs
        swing_highs = []
        for i in range(3, len(highs) - 3):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i-3] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2] and highs[i] > highs[i+3]:
                swing_highs.append((i, highs[i]))

        if len(swing_highs) < 3:
            return {'valid': False}

        # Look for pattern in recent swing highs
        recent = swing_highs[-5:] if len(swing_highs) >= 5 else swing_highs

        # Find head (highest peak)
        head_idx = max(range(len(recent)), key=lambda i: recent[i][1])

        if head_idx == 0 or head_idx == len(recent) - 1:
            return {'valid': False}

        head = recent[head_idx]
        left_shoulder = recent[head_idx - 1]
        right_shoulder = recent[head_idx + 1] if head_idx + 1 < len(recent) else None

        if right_shoulder is None:
            return {'valid': False}

        # Validate shoulders are approximately equal
        tolerance = left_shoulder[1] * self.hp['shoulder_tolerance']
        if abs(left_shoulder[1] - right_shoulder[1]) > tolerance:
            return {'valid': False}

        # Validate head is higher than shoulders
        avg_shoulder = (left_shoulder[1] + right_shoulder[1]) / 2
        if head[1] < avg_shoulder * self.hp['head_ratio_min']:
            return {'valid': False}

        # Calculate neckline
        left_trough_idx = range(left_shoulder[0], head[0])
        right_trough_idx = range(head[0], right_shoulder[0])

        if len(left_trough_idx) == 0 or len(right_trough_idx) == 0:
            return {'valid': False}

        left_trough = np.min(lows[list(left_trough_idx)])
        right_trough = np.min(lows[list(right_trough_idx)])
        neckline = (left_trough + right_trough) / 2

        return {
            'valid': True,
            'neckline': neckline,
            'head': head[1],
            'shoulders': avg_shoulder,
            'height': head[1] - neckline
        }

    def _detect_inverse_head_shoulders(self) -> dict:
        """Detect inverse head and shoulders (bullish) pattern"""
        lookback = self.hp['lookback']
        highs = self.candles[-lookback:, 3]
        lows = self.candles[-lookback:, 4]

        # Find swing lows
        swing_lows = []
        for i in range(3, len(lows) - 3):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i-3] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2] and lows[i] < lows[i+3]:
                swing_lows.append((i, lows[i]))

        if len(swing_lows) < 3:
            return {'valid': False}

        # Look for pattern in recent swing lows
        recent = swing_lows[-5:] if len(swing_lows) >= 5 else swing_lows

        # Find head (lowest trough)
        head_idx = min(range(len(recent)), key=lambda i: recent[i][1])

        if head_idx == 0 or head_idx == len(recent) - 1:
            return {'valid': False}

        head = recent[head_idx]
        left_shoulder = recent[head_idx - 1]
        right_shoulder = recent[head_idx + 1] if head_idx + 1 < len(recent) else None

        if right_shoulder is None:
            return {'valid': False}

        # Validate shoulders are approximately equal
        tolerance = left_shoulder[1] * self.hp['shoulder_tolerance']
        if abs(left_shoulder[1] - right_shoulder[1]) > tolerance:
            return {'valid': False}

        # Validate head is lower than shoulders
        avg_shoulder = (left_shoulder[1] + right_shoulder[1]) / 2
        if head[1] > avg_shoulder / self.hp['head_ratio_min']:
            return {'valid': False}

        # Calculate neckline
        left_peak_idx = range(left_shoulder[0], head[0])
        right_peak_idx = range(head[0], right_shoulder[0])

        if len(left_peak_idx) == 0 or len(right_peak_idx) == 0:
            return {'valid': False}

        left_peak = np.max(highs[list(left_peak_idx)])
        right_peak = np.max(highs[list(right_peak_idx)])
        neckline = (left_peak + right_peak) / 2

        return {
            'valid': True,
            'neckline': neckline,
            'head': head[1],
            'shoulders': avg_shoulder,
            'height': neckline - head[1]
        }

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        pattern = self._detect_inverse_head_shoulders()
        if not pattern['valid']:
            return False

        prev_close = self.candles[-2, 2]
        return prev_close < pattern['neckline'] and self.close > pattern['neckline']

    def should_short(self) -> bool:
        pattern = self._detect_head_shoulders()
        if not pattern['valid']:
            return False

        prev_close = self.candles[-2, 2]
        return prev_close > pattern['neckline'] and self.close < pattern['neckline']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        pattern = self._detect_inverse_head_shoulders()
        stop = pattern['head'] - (self.atr * self.hp['atr_multiplier_sl'])
        target = entry + pattern['height']
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        pattern = self._detect_head_shoulders()
        stop = pattern['head'] + (self.atr * self.hp['atr_multiplier_sl'])
        target = entry - pattern['height']
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
