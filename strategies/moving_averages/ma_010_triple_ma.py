"""
MA_010: Triple Moving Average Strategy
--------------------------------------
Uses three MAs for trend confirmation and entry timing.

Fast MA (signal), Medium MA (trend), Slow MA (filter)

Entry Long: Fast crosses Medium upward while both above Slow
Entry Short: Fast crosses Medium downward while both below Slow

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TripleMAStrategy(Strategy):
    """Triple Moving Average Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_010"
        self.strategy_name = "Triple MA"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 5, 'max': 20, 'default': 8},
            {'name': 'medium_period', 'type': int, 'min': 15, 'max': 50, 'default': 21},
            {'name': 'slow_period', 'type': int, 'min': 50, 'max': 200, 'default': 55},
            {'name': 'ma_type', 'type': str, 'default': 'ema'},  # 'sma' or 'ema'
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _get_ma(self, period: int, candles=None) -> float:
        """Get MA based on type setting"""
        if candles is None:
            candles = self.candles
        if self.hp.get('ma_type', 'ema') == 'sma':
            return ta.sma(candles, period=period)
        return ta.ema(candles, period=period)

    @property
    def fast_ma(self) -> float:
        return self._get_ma(self.hp['fast_period'])

    @property
    def medium_ma(self) -> float:
        return self._get_ma(self.hp['medium_period'])

    @property
    def slow_ma(self) -> float:
        return self._get_ma(self.hp['slow_period'])

    @property
    def fast_ma_prev(self) -> float:
        return self._get_ma(self.hp['fast_period'], self.candles[:-1])

    @property
    def medium_ma_prev(self) -> float:
        return self._get_ma(self.hp['medium_period'], self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _bullish_setup(self) -> bool:
        """Check for bullish triple MA setup"""
        # Fast crosses above medium
        cross_up = self.fast_ma_prev <= self.medium_ma_prev and self.fast_ma > self.medium_ma
        # Both above slow
        above_slow = self.fast_ma > self.slow_ma and self.medium_ma > self.slow_ma
        return cross_up and above_slow

    def _bearish_setup(self) -> bool:
        """Check for bearish triple MA setup"""
        # Fast crosses below medium
        cross_down = self.fast_ma_prev >= self.medium_ma_prev and self.fast_ma < self.medium_ma
        # Both below slow
        below_slow = self.fast_ma < self.slow_ma and self.medium_ma < self.slow_ma
        return cross_down and below_slow

    def should_long(self) -> bool:
        return self._bullish_setup()

    def should_short(self) -> bool:
        return self._bearish_setup()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = min(self.slow_ma, entry - (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'] * 2)),
        ]

    def go_short(self):
        entry = self.price
        stop = max(self.slow_ma, entry + (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'] * 2)),
        ]

    def update_position(self):
        # Exit on breakdown/breakout of slow MA
        if self.is_long and self.close < self.slow_ma:
            self.liquidate()
        elif self.is_short and self.close > self.slow_ma:
            self.liquidate()
