"""
MR_009: Gap Fade Strategy
-------------------------
Fade opening gaps expecting mean reversion.

Entry Long: After gap down (fade the gap)
Entry Short: After gap up (fade the gap)

Optimal Timeframes: 15m, 1h
Complexity: 4/10
Crypto Suitability: 6/10 (crypto trades 24/7, less gaps)
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class GapFade(Strategy):
    """Gap Fade Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MR_009"
        self.strategy_name = "Gap Fade"
        self.complexity = 4
        self.crypto_suitability = 6

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'gap_threshold', 'type': float, 'min': 0.5, 'max': 2.0, 'default': 1.0},
            {'name': 'fill_target', 'type': float, 'min': 0.5, 'max': 1.0, 'default': 0.75},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    @property
    def gap_pct(self) -> float:
        """Calculate gap percentage from previous close"""
        prev_close = self.candles[-2, 2]
        if prev_close == 0:
            return 0
        return ((self.open - prev_close) / prev_close) * 100

    @property
    def prev_close(self) -> float:
        return self.candles[-2, 2]

    @property
    def gap_up(self) -> bool:
        return self.gap_pct > self.hp['gap_threshold']

    @property
    def gap_down(self) -> bool:
        return self.gap_pct < -self.hp['gap_threshold']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Gap down, fade by going long
        return self.gap_down and self.close > self.open  # Reversal candle

    def should_short(self) -> bool:
        # Gap up, fade by going short
        return self.gap_up and self.close < self.open  # Reversal candle

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        # Target: partial gap fill
        gap_size = abs(self.open - self.prev_close)
        target = entry + (gap_size * self.hp['fill_target'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        # Target: partial gap fill
        gap_size = abs(self.open - self.prev_close)
        target = entry - (gap_size * self.hp['fill_target'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit if gap fills or reverses direction
        if self.is_long and self.close >= self.prev_close:
            self.liquidate()
        elif self.is_short and self.close <= self.prev_close:
            self.liquidate()
