"""
MA_007: Zero Lag EMA (ZLEMA) Strategy
-------------------------------------
ZLEMA attempts to eliminate lag by using a de-lagged data series.

ZLEMA = EMA(2 * price - price[lag], period)
where lag = (period - 1) / 2

Entry Long: ZLEMA crosses above EMA
Entry Short: ZLEMA crosses below EMA

Optimal Timeframes: 5m, 15m, 1h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ZLEMAStrategy(Strategy):
    """Zero Lag EMA Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_007"
        self.strategy_name = "ZLEMA"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'zlema_period', 'type': int, 'min': 8, 'max': 30, 'default': 14},
            {'name': 'ema_period', 'type': int, 'min': 15, 'max': 50, 'default': 28},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 2.5},
        ]

    def _calculate_zlema(self, period: int = None, candles=None) -> np.ndarray:
        """Calculate Zero Lag EMA (sequential)"""
        if candles is None:
            candles = self.candles
        if period is None:
            period = self.hp['zlema_period']

        close = candles[:, 2]
        lag = int((period - 1) / 2)

        # De-lagged series: 2 * price - price[lag]
        delagged = np.zeros(len(close))
        for i in range(lag, len(close)):
            delagged[i] = 2 * close[i] - close[i - lag]

        # Apply EMA to de-lagged series
        temp_candles = candles.copy()
        temp_candles[:, 2] = delagged
        zlema = ta.ema(temp_candles, period=period, sequential=True)

        return zlema

    @property
    def zlema(self) -> float:
        return self._calculate_zlema()[-1]

    @property
    def zlema_prev(self) -> float:
        return self._calculate_zlema()[-2]

    @property
    def reference_ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['ema_period'])

    @property
    def reference_ema_prev(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['ema_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _bullish_cross(self) -> bool:
        return self.zlema_prev <= self.reference_ema_prev and self.zlema > self.reference_ema

    def _bearish_cross(self) -> bool:
        return self.zlema_prev >= self.reference_ema_prev and self.zlema < self.reference_ema

    def should_long(self) -> bool:
        return self._bullish_cross()

    def should_short(self) -> bool:
        return self._bearish_cross()

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
        if self.is_long and self._bearish_cross():
            self.liquidate()
        elif self.is_short and self._bullish_cross():
            self.liquidate()
