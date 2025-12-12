"""
MOM_010: CCI Zero Line Cross Strategy
-------------------------------------
Trend-following using CCI zero line crossovers.

Entry Long: CCI crosses above 0
Entry Short: CCI crosses below 0

Optimal Timeframes: 1h, 4h
Complexity: 2/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class CCIZeroLine(Strategy):
    """CCI Zero Line Cross Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_010"
        self.strategy_name = "CCI Zero Line"
        self.complexity = 2
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'trend_ma_period', 'type': int, 'min': 50, 'max': 200, 'default': 100},
            {'name': 'use_trend_filter', 'type': bool, 'default': True},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    @property
    def cci(self) -> float:
        return ta.cci(self.candles, period=self.hp['period'])

    @property
    def cci_prev(self) -> float:
        return ta.cci(self.candles[:-1], period=self.hp['period'])

    @property
    def trend_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['trend_ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _uptrend(self) -> bool:
        if not self.hp.get('use_trend_filter', True):
            return True
        return self.close > self.trend_ma

    def _downtrend(self) -> bool:
        if not self.hp.get('use_trend_filter', True):
            return True
        return self.close < self.trend_ma

    def should_long(self) -> bool:
        crossed_above = self.cci_prev <= 0 and self.cci > 0
        return crossed_above and self._uptrend()

    def should_short(self) -> bool:
        crossed_below = self.cci_prev >= 0 and self.cci < 0
        return crossed_below and self._downtrend()

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
        # Exit on opposite crossover
        if self.is_long and self.cci < 0:
            self.liquidate()
        elif self.is_short and self.cci > 0:
            self.liquidate()
