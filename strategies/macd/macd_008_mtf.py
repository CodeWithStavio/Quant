"""
MACD_008: Multi-Timeframe MACD Strategy
---------------------------------------
Higher timeframe MACD for trend, lower timeframe for entry.

Entry Long: Higher TF MACD bullish AND Lower TF MACD bullish cross
Entry Short: Higher TF MACD bearish AND Lower TF MACD bearish cross

Note: Requires extra candles in routes.py for higher timeframe

Optimal Timeframes: 15m entry with 1h trend
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MACDMTF(Strategy):
    """Multi-Timeframe MACD Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MACD_008"
        self.strategy_name = "MTF MACD"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'trend_ma_period', 'type': int, 'min': 50, 'max': 200, 'default': 100},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _get_macd(self, candles=None):
        if candles is None:
            candles = self.candles
        return ta.macd(
            candles,
            fast_period=self.hp['fast_period'],
            slow_period=self.hp['slow_period'],
            signal_period=self.hp['signal_period']
        )

    @property
    def macd_line(self) -> float:
        macd, signal, hist = self._get_macd()
        return macd

    @property
    def signal_line(self) -> float:
        macd, signal, hist = self._get_macd()
        return signal

    @property
    def histogram(self) -> float:
        macd, signal, hist = self._get_macd()
        return hist

    @property
    def macd_line_prev(self) -> float:
        macd, signal, hist = self._get_macd(self.candles[:-1])
        return macd

    @property
    def signal_line_prev(self) -> float:
        macd, signal, hist = self._get_macd(self.candles[:-1])
        return signal

    @property
    def trend_ma(self) -> float:
        """Use longer MA as proxy for higher timeframe trend"""
        return ta.ema(self.candles, period=self.hp['trend_ma_period'])

    @property
    def trend_ma_slope(self) -> float:
        """Calculate slope of trend MA"""
        ma_seq = ta.ema(self.candles, period=self.hp['trend_ma_period'], sequential=True)
        return ma_seq[-1] - ma_seq[-5]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _higher_tf_bullish(self) -> bool:
        """Higher TF trend is bullish (using MA as proxy)"""
        return self.close > self.trend_ma and self.trend_ma_slope > 0

    def _higher_tf_bearish(self) -> bool:
        """Higher TF trend is bearish"""
        return self.close < self.trend_ma and self.trend_ma_slope < 0

    def _macd_bullish_cross(self) -> bool:
        return self.macd_line_prev <= self.signal_line_prev and self.macd_line > self.signal_line

    def _macd_bearish_cross(self) -> bool:
        return self.macd_line_prev >= self.signal_line_prev and self.macd_line < self.signal_line

    def should_long(self) -> bool:
        return self._higher_tf_bullish() and self._macd_bullish_cross()

    def should_short(self) -> bool:
        return self._higher_tf_bearish() and self._macd_bearish_cross()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = max(self.trend_ma * 0.98, entry - (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def go_short(self):
        entry = self.price
        stop = min(self.trend_ma * 1.02, entry + (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def update_position(self):
        # Exit if higher TF trend reverses
        if self.is_long and self._higher_tf_bearish():
            self.liquidate()
        elif self.is_short and self._higher_tf_bullish():
            self.liquidate()
