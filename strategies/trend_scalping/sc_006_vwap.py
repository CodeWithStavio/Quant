"""
SC_006: VWAP Scalp Strategy
---------------------------
Scalp bounces off VWAP.

Entry Long: Price bounces off VWAP from below
Entry Short: Price rejects VWAP from above

Optimal Timeframes: 1m, 5m, 15m
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VWAPScalp(Strategy):
    """VWAP Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_006"
        self.strategy_name = "VWAP Scalp"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'vwap_period', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'tolerance_pct', 'type': float, 'min': 0.05, 'max': 0.2, 'default': 0.1},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    @property
    def vwap(self) -> float:
        """Calculate VWAP"""
        period = self.hp['vwap_period']
        typical_price = (self.candles[-period:, 3] + self.candles[-period:, 4] + self.candles[-period:, 2]) / 3
        volume = self.candles[-period:, 5]

        total_vol = np.sum(volume)
        if total_vol == 0:
            return self.close

        return np.sum(typical_price * volume) / total_vol

    @property
    def near_vwap(self) -> bool:
        """Check if price is near VWAP"""
        tolerance = self.close * (self.hp['tolerance_pct'] / 100)
        return abs(self.close - self.vwap) <= tolerance

    @property
    def touched_vwap_from_below(self) -> bool:
        """Price came from below and touched VWAP"""
        prev_close = self.candles[-2, 2]
        return prev_close < self.vwap and self.low <= self.vwap

    @property
    def touched_vwap_from_above(self) -> bool:
        """Price came from above and touched VWAP"""
        prev_close = self.candles[-2, 2]
        return prev_close > self.vwap and self.high >= self.vwap

    def should_long(self) -> bool:
        # Bounce off VWAP from below
        return self.touched_vwap_from_below and self.close > self.vwap and self.close > self.open

    def should_short(self) -> bool:
        # Rejection at VWAP from above
        return self.touched_vwap_from_above and self.close < self.vwap and self.close < self.open

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry * (1 - self.hp['sl_pct'] / 100)
        target = entry * (1 + self.hp['tp_pct'] / 100)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry * (1 + self.hp['sl_pct'] / 100)
        target = entry * (1 - self.hp['tp_pct'] / 100)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
