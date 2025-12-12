"""
ONCHAIN_005: Network Value Proxy Strategy
-----------------------------------------
Approximate network value using price and volume metrics.

Entry Long: NVT ratio low (undervalued)
Entry Short: NVT ratio high (overvalued)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class NetworkValueProxy(Strategy):
    """Network Value Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ONCHAIN_005"
        self.strategy_name = "Network Value Proxy"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'low_nvt_percentile', 'type': float, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'high_nvt_percentile', 'type': float, 'min': 70, 'max': 85, 'default': 80},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_nvt_proxy(self) -> float:
        """Calculate NVT proxy: price / transaction volume proxy"""
        # Use trading volume as proxy for transaction volume
        avg_volume_value = np.mean(self.candles[-20:, 5] * self.candles[-20:, 2])
        if avg_volume_value == 0:
            return 1.0
        # NVT = Market Cap / Transaction Volume (proxy)
        return self.close / (avg_volume_value / self.close)

    def _get_nvt_percentile(self) -> float:
        """Get current NVT percentile"""
        lookback = self.hp['lookback']
        nvt_current = self._calculate_nvt_proxy()

        nvt_history = []
        for i in range(1, lookback + 1):
            if len(self.candles) > i + 20:
                vol_value = np.mean(self.candles[-20-i:-i, 5] * self.candles[-20-i:-i, 2])
                if vol_value > 0:
                    price = self.candles[-i, 2]
                    nvt = price / (vol_value / price)
                    nvt_history.append(nvt)

        if not nvt_history:
            return 50

        return np.sum(np.array(nvt_history) < nvt_current) / len(nvt_history) * 100

    @property
    def nvt_percentile(self) -> float:
        return self._get_nvt_percentile()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Low NVT = undervalued
        return self.nvt_percentile < self.hp['low_nvt_percentile']

    def should_short(self) -> bool:
        # High NVT = overvalued
        return self.nvt_percentile > self.hp['high_nvt_percentile']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit when NVT normalizes
        if self.is_long and self.nvt_percentile > 50:
            self.liquidate()
        elif self.is_short and self.nvt_percentile < 50:
            self.liquidate()
