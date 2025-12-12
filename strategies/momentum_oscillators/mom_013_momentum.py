"""
MOM_013: Momentum Indicator Strategy
------------------------------------
Simple momentum = Current Price - Price N periods ago

Entry Long: Momentum crosses above 0
Entry Short: Momentum crosses below 0

Optimal Timeframes: 15m, 1h, 4h
Complexity: 1/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MomentumIndicator(Strategy):
    """Momentum Indicator Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_013"
        self.strategy_name = "Momentum"
        self.complexity = 1
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 5, 'max': 20, 'default': 10},
            {'name': 'trend_filter', 'type': int, 'min': 50, 'max': 200, 'default': 100},
            {'name': 'use_trend_filter', 'type': bool, 'default': True},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 2.5},
        ]

    @property
    def momentum(self) -> float:
        close = self.candles[:, 2]
        period = self.hp['period']
        return close[-1] - close[-period-1]

    @property
    def momentum_prev(self) -> float:
        close = self.candles[:, 2]
        period = self.hp['period']
        return close[-2] - close[-period-2]

    @property
    def trend_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['trend_filter'])

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
        crossed = self.momentum_prev <= 0 and self.momentum > 0
        return crossed and self._uptrend()

    def should_short(self) -> bool:
        crossed = self.momentum_prev >= 0 and self.momentum < 0
        return crossed and self._downtrend()

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
        if self.is_long and self.momentum < 0:
            self.liquidate()
        elif self.is_short and self.momentum > 0:
            self.liquidate()
