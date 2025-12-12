"""
ICH_006: Ichimoku Kijun Bounce Strategy
---------------------------------------
Trade bounces off the Kijun-sen (Base Line).
Kijun acts as dynamic support/resistance.

Entry Long: Price bounces off Kijun from above
Entry Short: Price bounces off Kijun from below

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class IchimokuKijunBounce(Strategy):
    """Ichimoku Kijun Bounce Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ICH_006"
        self.strategy_name = "Ichimoku Kijun Bounce"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'kijun_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'senkou_b_period', 'type': int, 'min': 45, 'max': 60, 'default': 52},
            {'name': 'bounce_threshold', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_kijun(self, candles=None) -> float:
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]
        period = self.hp['kijun_period']

        return (np.max(high[-period:]) + np.min(low[-period:])) / 2

    @property
    def kijun(self) -> float:
        return self._calculate_kijun()

    @property
    def kijun_prev(self) -> float:
        return self._calculate_kijun(self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def near_kijun(self) -> bool:
        threshold = self.close * self.hp['bounce_threshold']
        return abs(self.close - self.kijun) < threshold

    @property
    def bounced_up_from_kijun(self) -> bool:
        """Price touched Kijun and bounced up"""
        prev_low = self.candles[-2, 4]
        touched = prev_low <= self.kijun_prev * 1.001
        bounced = self.close > self.kijun and self.close > self.open
        return touched and bounced

    @property
    def bounced_down_from_kijun(self) -> bool:
        """Price touched Kijun and bounced down"""
        prev_high = self.candles[-2, 3]
        touched = prev_high >= self.kijun_prev * 0.999
        bounced = self.close < self.kijun and self.close < self.open
        return touched and bounced

    @property
    def uptrend(self) -> bool:
        """Simple uptrend check"""
        return self.close > self.kijun

    @property
    def downtrend(self) -> bool:
        """Simple downtrend check"""
        return self.close < self.kijun

    def should_long(self) -> bool:
        return self.bounced_up_from_kijun

    def should_short(self) -> bool:
        return self.bounced_down_from_kijun

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.kijun - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = self.kijun + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        # Exit on Kijun cross
        if self.is_long and self.close < self.kijun:
            self.liquidate()
        elif self.is_short and self.close > self.kijun:
            self.liquidate()
