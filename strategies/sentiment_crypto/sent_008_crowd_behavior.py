"""
SENT_008: Crowd Behavior Strategy
---------------------------------
Detect crowd/herd behavior through volume and price patterns.

Entry Long: Crowd buying detected (momentum with volume)
Entry Short: Crowd selling detected (panic with volume)

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class CrowdBehavior(Strategy):
    """Crowd Behavior Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SENT_008"
        self.strategy_name = "Crowd Behavior"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'vol_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'vol_surge', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'price_move', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['vol_lookback']-1:-1, 5])

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def volume_ratio(self) -> float:
        return self.current_volume / self.avg_volume if self.avg_volume > 0 else 1

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def price_change_pct(self) -> float:
        """Price change as percentage of ATR"""
        return abs(self.close - self.open) / self.atr if self.atr > 0 else 0

    def _is_crowd_buying(self) -> bool:
        """Detect crowd buying pattern"""
        # High volume
        high_vol = self.volume_ratio > self.hp['vol_surge']

        # Significant upward move
        bullish = self.close > self.open
        big_move = self.price_change_pct > self.hp['price_move']

        # Momentum confirmation
        roc = ta.roc(self.candles, period=5)
        positive_mom = roc > 0

        return high_vol and bullish and big_move and positive_mom

    def _is_crowd_selling(self) -> bool:
        """Detect crowd selling/panic pattern"""
        # High volume
        high_vol = self.volume_ratio > self.hp['vol_surge']

        # Significant downward move
        bearish = self.close < self.open
        big_move = self.price_change_pct > self.hp['price_move']

        # Momentum confirmation
        roc = ta.roc(self.candles, period=5)
        negative_mom = roc < 0

        return high_vol and bearish and big_move and negative_mom

    def should_long(self) -> bool:
        return self._is_crowd_buying()

    def should_short(self) -> bool:
        return self._is_crowd_selling()

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
        # Exit on volume exhaustion
        if self.volume_ratio < 0.5:
            self.liquidate()
