"""
MA_002: Exponential Moving Average Crossover Strategy
-----------------------------------------------------
EMA crossover for faster trend following with reduced lag.

Entry Long: Fast EMA crosses above Slow EMA
Entry Short: Fast EMA crosses below Slow EMA

Optimal Timeframes: 5m, 15m, 1h
Complexity: 2/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class EMACrossover(Strategy):
    """Exponential Moving Average Crossover Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_002"
        self.strategy_name = "EMA Crossover"
        self.complexity = 2
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 5, 'max': 30, 'default': 8},
            {'name': 'slow_period', 'type': int, 'min': 15, 'max': 100, 'default': 21},
            {'name': 'trend_filter_period', 'type': int, 'min': 50, 'max': 200, 'default': 100},
            {'name': 'use_trend_filter', 'type': bool, 'default': True},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 4.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 6.0, 'default': 3.0},
        ]

    @property
    def fast_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['fast_period'])

    @property
    def slow_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['slow_period'])

    @property
    def trend_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['trend_filter_period'])

    @property
    def fast_ema_prev(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['fast_period'])

    @property
    def slow_ema_prev(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['slow_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _bullish_cross(self) -> bool:
        """Check for bullish EMA crossover"""
        return self.fast_ema_prev <= self.slow_ema_prev and self.fast_ema > self.slow_ema

    def _bearish_cross(self) -> bool:
        """Check for bearish EMA crossover"""
        return self.fast_ema_prev >= self.slow_ema_prev and self.fast_ema < self.slow_ema

    def _trend_is_up(self) -> bool:
        """Check if in uptrend using trend filter"""
        if not self.hp['use_trend_filter']:
            return True
        return self.close > self.trend_ema

    def _trend_is_down(self) -> bool:
        """Check if in downtrend using trend filter"""
        if not self.hp['use_trend_filter']:
            return True
        return self.close < self.trend_ema

    def should_long(self) -> bool:
        return self._bullish_cross() and self._trend_is_up()

    def should_short(self) -> bool:
        return self._bearish_cross() and self._trend_is_down()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.4, entry + (self.atr * self.hp['atr_multiplier_tp'])),
            (0.3, entry + (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
            (0.3, entry + (self.atr * self.hp['atr_multiplier_tp'] * 2)),
        ]

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.4, entry - (self.atr * self.hp['atr_multiplier_tp'])),
            (0.3, entry - (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
            (0.3, entry - (self.atr * self.hp['atr_multiplier_tp'] * 2)),
        ]

    def update_position(self):
        # Exit on opposite crossover
        if self.is_long and self._bearish_cross():
            self.liquidate()
        elif self.is_short and self._bullish_cross():
            self.liquidate()
