"""
VOL_003: VWAP Bounce Strategy
-----------------------------
Trade bounces off the Volume Weighted Average Price (VWAP).
VWAP is a key intraday level used by institutional traders.

Entry Long: Price bounces off VWAP from below
Entry Short: Price bounces off VWAP from above

Optimal Timeframes: 5m, 15m, 1h
Complexity: 3/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VWAPBounce(Strategy):
    """VWAP Bounce Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_003"
        self.strategy_name = "VWAP Bounce"
        self.complexity = 3
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'vwap_period', 'type': int, 'min': 20, 'max': 100, 'default': 50},
            {'name': 'bounce_threshold', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _calculate_vwap(self, candles=None):
        """Calculate VWAP"""
        if candles is None:
            candles = self.candles

        period = min(self.hp['vwap_period'], len(candles))
        candles = candles[-period:]

        typical_price = (candles[:, 3] + candles[:, 4] + candles[:, 2]) / 3  # (high + low + close) / 3
        volume = candles[:, 5]

        cumulative_tp_vol = np.cumsum(typical_price * volume)
        cumulative_vol = np.cumsum(volume)

        # Avoid division by zero
        cumulative_vol = np.where(cumulative_vol == 0, 1, cumulative_vol)

        vwap = cumulative_tp_vol / cumulative_vol
        return vwap[-1]

    @property
    def vwap(self) -> float:
        return self._calculate_vwap()

    @property
    def vwap_prev(self) -> float:
        return self._calculate_vwap(self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def near_vwap(self) -> bool:
        """Check if price is near VWAP"""
        threshold = self.vwap * self.hp['bounce_threshold']
        return abs(self.close - self.vwap) < threshold

    @property
    def crossed_above_vwap(self) -> bool:
        """Price crossed above VWAP"""
        prev_close = self.candles[-2, 2]
        return prev_close <= self.vwap_prev and self.close > self.vwap

    @property
    def crossed_below_vwap(self) -> bool:
        """Price crossed below VWAP"""
        prev_close = self.candles[-2, 2]
        return prev_close >= self.vwap_prev and self.close < self.vwap

    @property
    def bounced_up_from_vwap(self) -> bool:
        """Price touched VWAP and bounced up"""
        prev_low = self.candles[-2, 4]
        touched_vwap = prev_low <= self.vwap_prev
        bounced_up = self.close > self.vwap and self.close > self.open
        return touched_vwap and bounced_up

    @property
    def bounced_down_from_vwap(self) -> bool:
        """Price touched VWAP and bounced down"""
        prev_high = self.candles[-2, 3]
        touched_vwap = prev_high >= self.vwap_prev
        bounced_down = self.close < self.vwap and self.close < self.open
        return touched_vwap and bounced_down

    def should_long(self) -> bool:
        return self.bounced_up_from_vwap or self.crossed_above_vwap

    def should_short(self) -> bool:
        return self.bounced_down_from_vwap or self.crossed_below_vwap

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
        # Exit on VWAP cross
        if self.is_long and self.close < self.vwap:
            self.liquidate()
        elif self.is_short and self.close > self.vwap:
            self.liquidate()
