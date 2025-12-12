"""
ICH_002: Ichimoku TK Cross Strategy
-----------------------------------
Tenkan-sen / Kijun-sen crossover signals.
TK cross above cloud = strong bullish.
TK cross below cloud = strong bearish.

Entry Long: Tenkan crosses above Kijun
Entry Short: Tenkan crosses below Kijun

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class IchimokuTKCross(Strategy):
    """Ichimoku TK Cross Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ICH_002"
        self.strategy_name = "Ichimoku TK Cross"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'tenkan_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'kijun_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'senkou_b_period', 'type': int, 'min': 45, 'max': 60, 'default': 52},
            {'name': 'require_cloud_confirm', 'type': bool, 'default': True},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_ichimoku(self, candles=None):
        """Calculate Ichimoku components"""
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]

        tenkan_period = self.hp['tenkan_period']
        kijun_period = self.hp['kijun_period']
        senkou_b_period = self.hp['senkou_b_period']

        tenkan = (np.max(high[-tenkan_period:]) + np.min(low[-tenkan_period:])) / 2
        kijun = (np.max(high[-kijun_period:]) + np.min(low[-kijun_period:])) / 2
        senkou_a = (tenkan + kijun) / 2
        senkou_b = (np.max(high[-senkou_b_period:]) + np.min(low[-senkou_b_period:])) / 2

        return tenkan, kijun, senkou_a, senkou_b

    @property
    def tenkan(self) -> float:
        tenkan, _, _, _ = self._calculate_ichimoku()
        return tenkan

    @property
    def kijun(self) -> float:
        _, kijun, _, _ = self._calculate_ichimoku()
        return kijun

    @property
    def tenkan_prev(self) -> float:
        tenkan, _, _, _ = self._calculate_ichimoku(self.candles[:-1])
        return tenkan

    @property
    def kijun_prev(self) -> float:
        _, kijun, _, _ = self._calculate_ichimoku(self.candles[:-1])
        return kijun

    @property
    def cloud_top(self) -> float:
        _, _, senkou_a, senkou_b = self._calculate_ichimoku()
        return max(senkou_a, senkou_b)

    @property
    def cloud_bottom(self) -> float:
        _, _, senkou_a, senkou_b = self._calculate_ichimoku()
        return min(senkou_a, senkou_b)

    @property
    def above_cloud(self) -> bool:
        return self.close > self.cloud_top

    @property
    def below_cloud(self) -> bool:
        return self.close < self.cloud_bottom

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def tk_bullish_cross(self) -> bool:
        """Tenkan crosses above Kijun"""
        return self.tenkan_prev <= self.kijun_prev and self.tenkan > self.kijun

    @property
    def tk_bearish_cross(self) -> bool:
        """Tenkan crosses below Kijun"""
        return self.tenkan_prev >= self.kijun_prev and self.tenkan < self.kijun

    def should_long(self) -> bool:
        if self.hp['require_cloud_confirm']:
            return self.tk_bullish_cross and self.above_cloud
        return self.tk_bullish_cross

    def should_short(self) -> bool:
        if self.hp['require_cloud_confirm']:
            return self.tk_bearish_cross and self.below_cloud
        return self.tk_bearish_cross

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
        # Exit on opposite TK cross
        if self.is_long and self.tk_bearish_cross:
            self.liquidate()
        elif self.is_short and self.tk_bullish_cross:
            self.liquidate()
