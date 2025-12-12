"""
ICH_003: Ichimoku Kumo Breakout Strategy
----------------------------------------
Trade breakouts from the Ichimoku cloud (Kumo).
Strong signals when price breaks through cloud.

Entry Long: Price breaks above cloud top
Entry Short: Price breaks below cloud bottom

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class IchimokuKumoBreakout(Strategy):
    """Ichimoku Kumo Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ICH_003"
        self.strategy_name = "Ichimoku Kumo Breakout"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'tenkan_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'kijun_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'senkou_b_period', 'type': int, 'min': 45, 'max': 60, 'default': 52},
            {'name': 'min_cloud_thickness', 'type': float, 'min': 0.001, 'max': 0.01, 'default': 0.005},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _calculate_ichimoku(self, candles=None):
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]

        tenkan = (np.max(high[-self.hp['tenkan_period']:]) + np.min(low[-self.hp['tenkan_period']:])) / 2
        kijun = (np.max(high[-self.hp['kijun_period']:]) + np.min(low[-self.hp['kijun_period']:])) / 2
        senkou_a = (tenkan + kijun) / 2
        senkou_b = (np.max(high[-self.hp['senkou_b_period']:]) + np.min(low[-self.hp['senkou_b_period']:])) / 2

        return tenkan, kijun, senkou_a, senkou_b

    @property
    def cloud_top(self) -> float:
        _, _, senkou_a, senkou_b = self._calculate_ichimoku()
        return max(senkou_a, senkou_b)

    @property
    def cloud_bottom(self) -> float:
        _, _, senkou_a, senkou_b = self._calculate_ichimoku()
        return min(senkou_a, senkou_b)

    @property
    def cloud_thickness(self) -> float:
        return (self.cloud_top - self.cloud_bottom) / self.close

    @property
    def prev_cloud_top(self) -> float:
        _, _, senkou_a, senkou_b = self._calculate_ichimoku(self.candles[:-1])
        return max(senkou_a, senkou_b)

    @property
    def prev_cloud_bottom(self) -> float:
        _, _, senkou_a, senkou_b = self._calculate_ichimoku(self.candles[:-1])
        return min(senkou_a, senkou_b)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def breakout_up(self) -> bool:
        prev_close = self.candles[-2, 2]
        return prev_close <= self.prev_cloud_top and self.close > self.cloud_top

    @property
    def breakout_down(self) -> bool:
        prev_close = self.candles[-2, 2]
        return prev_close >= self.prev_cloud_bottom and self.close < self.cloud_bottom

    def should_long(self) -> bool:
        return self.breakout_up and self.cloud_thickness >= self.hp['min_cloud_thickness']

    def should_short(self) -> bool:
        return self.breakout_down and self.cloud_thickness >= self.hp['min_cloud_thickness']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.cloud_bottom - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.cloud_top + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long and self.close < self.cloud_bottom:
            self.liquidate()
        elif self.is_short and self.close > self.cloud_top:
            self.liquidate()
