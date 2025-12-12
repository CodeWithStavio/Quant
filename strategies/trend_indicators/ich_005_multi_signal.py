"""
ICH_005: Ichimoku Multi-Signal Strategy
---------------------------------------
Combines multiple Ichimoku signals for high-probability entries.
Requires TK cross + cloud position + Chikou confirmation.

Entry Long: All bullish signals aligned
Entry Short: All bearish signals aligned

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class IchimokuMultiSignal(Strategy):
    """Ichimoku Multi-Signal Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ICH_005"
        self.strategy_name = "Ichimoku Multi-Signal"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'tenkan_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'kijun_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'senkou_b_period', 'type': int, 'min': 45, 'max': 60, 'default': 52},
            {'name': 'displacement', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'min_signals', 'type': int, 'min': 3, 'max': 5, 'default': 4},
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
    def tenkan(self) -> float:
        tenkan, _, _, _ = self._calculate_ichimoku()
        return tenkan

    @property
    def kijun(self) -> float:
        _, kijun, _, _ = self._calculate_ichimoku()
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
    def past_price(self) -> float:
        displacement = self.hp['displacement']
        if len(self.candles) > displacement:
            return self.candles[-displacement, 2]
        return self.close

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _count_bullish_signals(self) -> int:
        """Count number of bullish Ichimoku signals"""
        count = 0

        # Signal 1: Price above cloud
        if self.close > self.cloud_top:
            count += 1

        # Signal 2: Tenkan above Kijun
        if self.tenkan > self.kijun:
            count += 1

        # Signal 3: Chikou above past price
        if self.close > self.past_price:
            count += 1

        # Signal 4: Price above Kijun
        if self.close > self.kijun:
            count += 1

        # Signal 5: Green cloud (Senkou A > Senkou B)
        _, _, senkou_a, senkou_b = self._calculate_ichimoku()
        if senkou_a > senkou_b:
            count += 1

        return count

    def _count_bearish_signals(self) -> int:
        """Count number of bearish Ichimoku signals"""
        count = 0

        # Signal 1: Price below cloud
        if self.close < self.cloud_bottom:
            count += 1

        # Signal 2: Tenkan below Kijun
        if self.tenkan < self.kijun:
            count += 1

        # Signal 3: Chikou below past price
        if self.close < self.past_price:
            count += 1

        # Signal 4: Price below Kijun
        if self.close < self.kijun:
            count += 1

        # Signal 5: Red cloud (Senkou A < Senkou B)
        _, _, senkou_a, senkou_b = self._calculate_ichimoku()
        if senkou_a < senkou_b:
            count += 1

        return count

    def should_long(self) -> bool:
        return self._count_bullish_signals() >= self.hp['min_signals']

    def should_short(self) -> bool:
        return self._count_bearish_signals() >= self.hp['min_signals']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = min(self.kijun, self.cloud_bottom) - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = max(self.kijun, self.cloud_top) + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long and self._count_bullish_signals() < 2:
            self.liquidate()
        elif self.is_short and self._count_bearish_signals() < 2:
            self.liquidate()
