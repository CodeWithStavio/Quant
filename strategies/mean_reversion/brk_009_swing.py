"""
BRK_009: Swing Breakout Strategy
--------------------------------
Trade breakouts of swing highs and lows.

Entry Long: Price breaks above recent swing high
Entry Short: Price breaks below recent swing low

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SwingBreakout(Strategy):
    """Swing Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_009"
        self.strategy_name = "Swing Breakout"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'swing_lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'breakout_confirm', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _find_swing_high(self) -> float:
        """Find most recent swing high"""
        lookback = self.hp['swing_lookback']
        highs = self.candles[-lookback:, 3]

        for i in range(len(highs) - 3, 1, -1):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                return highs[i]

        return np.max(highs)

    def _find_swing_low(self) -> float:
        """Find most recent swing low"""
        lookback = self.hp['swing_lookback']
        lows = self.candles[-lookback:, 4]

        for i in range(len(lows) - 3, 1, -1):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                return lows[i]

        return np.min(lows)

    @property
    def swing_high(self) -> float:
        return self._find_swing_high()

    @property
    def swing_low(self) -> float:
        return self._find_swing_low()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]
        return prev_close <= self.swing_high and self.close > self.swing_high + confirm

    def should_short(self) -> bool:
        confirm = self.close * self.hp['breakout_confirm']
        prev_close = self.candles[-2, 2]
        return prev_close >= self.swing_low and self.close < self.swing_low - confirm

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.swing_low - (self.atr * 0.5)
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = self.swing_high + (self.atr * 0.5)
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
