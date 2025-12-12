"""
MA_006: Volume Weighted Moving Average (VWMA) Strategy
------------------------------------------------------
VWMA weights price by volume, giving more importance to high-volume periods.

VWMA = SUM(Price * Volume) / SUM(Volume)

Entry Long: Price crosses above VWMA with rising volume
Entry Short: Price crosses below VWMA with rising volume

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VWMAStrategy(Strategy):
    """Volume Weighted Moving Average Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_006"
        self.strategy_name = "VWMA"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'vwma_period', 'type': int, 'min': 10, 'max': 50, 'default': 20},
            {'name': 'volume_threshold', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.2},
            {'name': 'sma_period', 'type': int, 'min': 50, 'max': 200, 'default': 100},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 2.5},
        ]

    def _calculate_vwma(self, period: int = None, candles=None) -> np.ndarray:
        """Calculate VWMA (sequential)"""
        if candles is None:
            candles = self.candles
        if period is None:
            period = self.hp['vwma_period']

        close = candles[:, 2]
        volume = candles[:, 5]

        vwma = np.zeros(len(close))
        for i in range(period - 1, len(close)):
            pv_sum = np.sum(close[i-period+1:i+1] * volume[i-period+1:i+1])
            v_sum = np.sum(volume[i-period+1:i+1])
            vwma[i] = pv_sum / v_sum if v_sum > 0 else close[i]

        return vwma

    @property
    def vwma(self) -> float:
        return self._calculate_vwma()[-1]

    @property
    def vwma_prev(self) -> float:
        return self._calculate_vwma()[-2]

    @property
    def volume_sma(self) -> float:
        return ta.sma(self.candles, period=20, source_type='volume')

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def volume_increasing(self) -> bool:
        return self.current_volume > self.volume_sma * self.hp['volume_threshold']

    @property
    def trend_sma(self) -> float:
        return ta.sma(self.candles, period=self.hp['sma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _price_crossed_above(self) -> bool:
        close = self.candles[:, 2]
        vwma = self._calculate_vwma()
        return close[-2] <= vwma[-2] and close[-1] > vwma[-1]

    def _price_crossed_below(self) -> bool:
        close = self.candles[:, 2]
        vwma = self._calculate_vwma()
        return close[-2] >= vwma[-2] and close[-1] < vwma[-1]

    def should_long(self) -> bool:
        return (self._price_crossed_above() and
                self.volume_increasing and
                self.close > self.trend_sma)

    def should_short(self) -> bool:
        return (self._price_crossed_below() and
                self.volume_increasing and
                self.close < self.trend_sma)

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
        # Exit when price crosses back through VWMA
        if self.is_long and self._price_crossed_below():
            self.liquidate()
        elif self.is_short and self._price_crossed_above():
            self.liquidate()
