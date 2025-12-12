"""
SAR_002: SAR + MA Filter Strategy
---------------------------------
Parabolic SAR signals filtered by MA trend.
Only trade SAR signals in direction of MA trend.

Entry Long: SAR bullish + price above MA
Entry Short: SAR bearish + price below MA

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SARMAFilter(Strategy):
    """SAR + MA Filter Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SAR_002"
        self.strategy_name = "SAR + MA Filter"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'acceleration', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'maximum', 'type': float, 'min': 0.15, 'max': 0.25, 'default': 0.2},
            {'name': 'ma_period', 'type': int, 'min': 50, 'max': 200, 'default': 100},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_sar(self):
        high = self.candles[:, 3]
        low = self.candles[:, 4]
        af = self.hp['acceleration']
        max_af = self.hp['maximum']

        sar = np.zeros(len(self.candles))
        trend = np.zeros(len(self.candles))
        ep = np.zeros(len(self.candles))
        af_vals = np.zeros(len(self.candles))

        sar[0] = low[0]
        trend[0] = 1
        ep[0] = high[0]
        af_vals[0] = af

        for i in range(1, len(self.candles)):
            if trend[i-1] == 1:
                sar[i] = sar[i-1] + af_vals[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = min(sar[i], low[i-1], low[max(0, i-2)] if i > 1 else low[i-1])

                if low[i] < sar[i]:
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af_vals[i] = af
                else:
                    trend[i] = 1
                    if high[i] > ep[i-1]:
                        ep[i] = high[i]
                        af_vals[i] = min(af_vals[i-1] + af, max_af)
                    else:
                        ep[i] = ep[i-1]
                        af_vals[i] = af_vals[i-1]
            else:
                sar[i] = sar[i-1] + af_vals[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = max(sar[i], high[i-1], high[max(0, i-2)] if i > 1 else high[i-1])

                if high[i] > sar[i]:
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af_vals[i] = af
                else:
                    trend[i] = -1
                    if low[i] < ep[i-1]:
                        ep[i] = low[i]
                        af_vals[i] = min(af_vals[i-1] + af, max_af)
                    else:
                        ep[i] = ep[i-1]
                        af_vals[i] = af_vals[i-1]

        return sar, trend

    @property
    def sar(self) -> float:
        sar, _ = self._calculate_sar()
        return sar[-1]

    @property
    def trend(self) -> int:
        _, trend = self._calculate_sar()
        return int(trend[-1])

    @property
    def trend_prev(self) -> int:
        _, trend = self._calculate_sar()
        return int(trend[-2]) if len(trend) > 1 else int(trend[-1])

    @property
    def ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def sar_bullish_flip(self) -> bool:
        return self.trend_prev == -1 and self.trend == 1

    @property
    def sar_bearish_flip(self) -> bool:
        return self.trend_prev == 1 and self.trend == -1

    @property
    def above_ma(self) -> bool:
        return self.close > self.ma

    @property
    def below_ma(self) -> bool:
        return self.close < self.ma

    def should_long(self) -> bool:
        return self.sar_bullish_flip and self.above_ma

    def should_short(self) -> bool:
        return self.sar_bearish_flip and self.below_ma

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
        if self.is_long and (self.trend == -1 or self.below_ma):
            self.liquidate()
        elif self.is_short and (self.trend == 1 or self.above_ma):
            self.liquidate()
