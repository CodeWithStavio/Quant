"""
TF_003: Supertrend Following Strategy
-------------------------------------
Follow the Supertrend indicator for trend direction.

Entry Long: Supertrend turns bullish
Entry Short: Supertrend turns bearish

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SupertrendFollowing(Strategy):
    """Supertrend Following Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_003"
        self.strategy_name = "Supertrend Following"
        self.complexity = 3
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'atr_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'multiplier', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _supertrend(self, candles=None):
        """Calculate Supertrend"""
        if candles is None:
            candles = self.candles

        atr = ta.atr(candles, period=self.hp['atr_period'])
        hl2 = (candles[-1, 3] + candles[-1, 4]) / 2

        upper_band = hl2 + (self.hp['multiplier'] * atr)
        lower_band = hl2 - (self.hp['multiplier'] * atr)

        # Determine trend
        close = candles[-1, 2]
        prev_close = candles[-2, 2]

        # Simplified supertrend calculation
        if close > upper_band:
            return 'bullish', lower_band
        elif close < lower_band:
            return 'bearish', upper_band
        else:
            # Continue previous trend
            if prev_close > (candles[-2, 3] + candles[-2, 4]) / 2:
                return 'bullish', lower_band
            else:
                return 'bearish', upper_band

    @property
    def supertrend_direction(self) -> str:
        direction, _ = self._supertrend()
        return direction

    @property
    def supertrend_value(self) -> float:
        _, value = self._supertrend()
        return value

    @property
    def prev_direction(self) -> str:
        direction, _ = self._supertrend(self.candles[:-1])
        return direction

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Supertrend just turned bullish
        return self.supertrend_direction == 'bullish' and self.prev_direction == 'bearish'

    def should_short(self) -> bool:
        # Supertrend just turned bearish
        return self.supertrend_direction == 'bearish' and self.prev_direction == 'bullish'

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.supertrend_value - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.supertrend_value + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit on supertrend reversal
        if self.is_long and self.supertrend_direction == 'bearish':
            self.liquidate()
        elif self.is_short and self.supertrend_direction == 'bullish':
            self.liquidate()
