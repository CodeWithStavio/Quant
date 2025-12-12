"""
VOL_001: OBV Trend Strategy
---------------------------
On-Balance Volume (OBV) trend following.
OBV rising with price = bullish confirmation.
OBV falling with price = bearish confirmation.

Entry Long: OBV above MA and rising
Entry Short: OBV below MA and falling

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class OBVTrend(Strategy):
    """OBV Trend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_001"
        self.strategy_name = "OBV Trend"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'obv_ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'price_ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_obv(self, candles=None):
        """Calculate On-Balance Volume"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]
        volume = candles[:, 5]

        obv = np.zeros(len(candles))
        obv[0] = volume[0]

        for i in range(1, len(candles)):
            if close[i] > close[i-1]:
                obv[i] = obv[i-1] + volume[i]
            elif close[i] < close[i-1]:
                obv[i] = obv[i-1] - volume[i]
            else:
                obv[i] = obv[i-1]

        return obv

    @property
    def obv(self) -> float:
        obv_series = self._calculate_obv()
        return obv_series[-1]

    @property
    def obv_prev(self) -> float:
        obv_series = self._calculate_obv()
        return obv_series[-2] if len(obv_series) > 1 else obv_series[-1]

    @property
    def obv_ma(self) -> float:
        obv_series = self._calculate_obv()
        period = self.hp['obv_ma_period']
        return np.mean(obv_series[-period:])

    @property
    def price_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['price_ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def obv_rising(self) -> bool:
        return self.obv > self.obv_prev

    @property
    def obv_falling(self) -> bool:
        return self.obv < self.obv_prev

    @property
    def obv_above_ma(self) -> bool:
        return self.obv > self.obv_ma

    @property
    def obv_below_ma(self) -> bool:
        return self.obv < self.obv_ma

    def should_long(self) -> bool:
        return self.obv_above_ma and self.obv_rising and self.close > self.price_ma

    def should_short(self) -> bool:
        return self.obv_below_ma and self.obv_falling and self.close < self.price_ma

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
        # Exit on OBV reversal
        if self.is_long and self.obv_below_ma and self.obv_falling:
            self.liquidate()
        elif self.is_short and self.obv_above_ma and self.obv_rising:
            self.liquidate()
