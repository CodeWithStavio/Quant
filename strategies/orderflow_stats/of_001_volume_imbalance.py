"""
OF_001: Volume Imbalance Strategy
---------------------------------
Trade based on buy/sell volume imbalance.

Entry Long: Strong buying imbalance
Entry Short: Strong selling imbalance

Optimal Timeframes: 5m, 15m, 1h
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolumeImbalance(Strategy):
    """Volume Imbalance Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "OF_001"
        self.strategy_name = "Volume Imbalance"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'imbalance_threshold', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'consecutive_bars', 'type': int, 'min': 2, 'max': 5, 'default': 3},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _estimate_buy_volume(self, idx: int) -> float:
        """Estimate buying volume based on price action"""
        candle = self.candles[idx]
        high, low, close, open_price, volume = candle[3], candle[4], candle[2], candle[1], candle[5]

        if high == low:
            return volume * 0.5

        # Buy volume estimated by close position in range
        buy_ratio = (close - low) / (high - low)
        return volume * buy_ratio

    def _estimate_sell_volume(self, idx: int) -> float:
        """Estimate selling volume"""
        candle = self.candles[idx]
        volume = candle[5]
        return volume - self._estimate_buy_volume(idx)

    def _calculate_imbalance(self) -> float:
        """Calculate volume imbalance ratio"""
        lookback = self.hp['lookback']
        buy_vol = sum(self._estimate_buy_volume(-i) for i in range(1, lookback + 1))
        sell_vol = sum(self._estimate_sell_volume(-i) for i in range(1, lookback + 1))

        if sell_vol == 0:
            return float('inf') if buy_vol > 0 else 1
        return buy_vol / sell_vol

    def _count_consecutive_buying(self) -> int:
        """Count consecutive bars with buying imbalance"""
        count = 0
        for i in range(1, 10):
            buy = self._estimate_buy_volume(-i)
            sell = self._estimate_sell_volume(-i)
            if buy > sell * 1.2:
                count += 1
            else:
                break
        return count

    def _count_consecutive_selling(self) -> int:
        """Count consecutive bars with selling imbalance"""
        count = 0
        for i in range(1, 10):
            buy = self._estimate_buy_volume(-i)
            sell = self._estimate_sell_volume(-i)
            if sell > buy * 1.2:
                count += 1
            else:
                break
        return count

    @property
    def imbalance(self) -> float:
        return self._calculate_imbalance()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        strong_buy = self.imbalance > self.hp['imbalance_threshold']
        consecutive = self._count_consecutive_buying() >= self.hp['consecutive_bars']
        return strong_buy and consecutive

    def should_short(self) -> bool:
        strong_sell = self.imbalance < (1 / self.hp['imbalance_threshold'])
        consecutive = self._count_consecutive_selling() >= self.hp['consecutive_bars']
        return strong_sell and consecutive

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
        # Exit on imbalance reversal
        if self.is_long and self.imbalance < 1:
            self.liquidate()
        elif self.is_short and self.imbalance > 1:
            self.liquidate()
