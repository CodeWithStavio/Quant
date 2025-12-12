"""
ICH_001: Ichimoku Cloud Crossover Strategy
------------------------------------------
Classic Ichimoku cloud-based trading.
Price above cloud = bullish, below = bearish.

Entry Long: Price crosses above cloud
Entry Short: Price crosses below cloud

Optimal Timeframes: 4h, 1d
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class IchimokuCloudCrossover(Strategy):
    """Ichimoku Cloud Crossover Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ICH_001"
        self.strategy_name = "Ichimoku Cloud Crossover"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'tenkan_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'kijun_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'senkou_b_period', 'type': int, 'min': 45, 'max': 60, 'default': 52},
            {'name': 'displacement', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _calculate_ichimoku(self, candles=None):
        """Calculate Ichimoku components"""
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]
        close = candles[:, 2]

        tenkan_period = self.hp['tenkan_period']
        kijun_period = self.hp['kijun_period']
        senkou_b_period = self.hp['senkou_b_period']

        # Tenkan-sen (Conversion Line)
        tenkan = (np.max(high[-tenkan_period:]) + np.min(low[-tenkan_period:])) / 2

        # Kijun-sen (Base Line)
        kijun = (np.max(high[-kijun_period:]) + np.min(low[-kijun_period:])) / 2

        # Senkou Span A (Leading Span A)
        senkou_a = (tenkan + kijun) / 2

        # Senkou Span B (Leading Span B)
        senkou_b = (np.max(high[-senkou_b_period:]) + np.min(low[-senkou_b_period:])) / 2

        # Chikou Span (Lagging Span) - close shifted back
        chikou = close[-1]

        return tenkan, kijun, senkou_a, senkou_b, chikou

    @property
    def ichimoku(self):
        return self._calculate_ichimoku()

    @property
    def tenkan(self) -> float:
        tenkan, _, _, _, _ = self.ichimoku
        return tenkan

    @property
    def kijun(self) -> float:
        _, kijun, _, _, _ = self.ichimoku
        return kijun

    @property
    def senkou_a(self) -> float:
        _, _, senkou_a, _, _ = self.ichimoku
        return senkou_a

    @property
    def senkou_b(self) -> float:
        _, _, _, senkou_b, _ = self.ichimoku
        return senkou_b

    @property
    def cloud_top(self) -> float:
        return max(self.senkou_a, self.senkou_b)

    @property
    def cloud_bottom(self) -> float:
        return min(self.senkou_a, self.senkou_b)

    @property
    def above_cloud(self) -> bool:
        return self.close > self.cloud_top

    @property
    def below_cloud(self) -> bool:
        return self.close < self.cloud_bottom

    @property
    def in_cloud(self) -> bool:
        return self.cloud_bottom <= self.close <= self.cloud_top

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _was_in_or_below_cloud(self) -> bool:
        """Check if previous bar was in or below cloud"""
        prev_close = self.candles[-2, 2]
        return prev_close <= self.cloud_top

    def _was_in_or_above_cloud(self) -> bool:
        """Check if previous bar was in or above cloud"""
        prev_close = self.candles[-2, 2]
        return prev_close >= self.cloud_bottom

    def should_long(self) -> bool:
        # Price crosses above cloud
        return self._was_in_or_below_cloud() and self.above_cloud

    def should_short(self) -> bool:
        # Price crosses below cloud
        return self._was_in_or_above_cloud() and self.below_cloud

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
        # Exit when price enters cloud
        if self.is_long and self.in_cloud:
            self.liquidate()
        elif self.is_short and self.in_cloud:
            self.liquidate()
