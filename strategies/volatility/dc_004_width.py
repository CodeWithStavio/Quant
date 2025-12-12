"""
DC_004: Donchian Width Volatility Strategy
------------------------------------------
Uses Donchian Channel width to gauge volatility.
Trade breakouts when width is expanding.

Entry Long: Break above upper with expanding width
Entry Short: Break below lower with expanding width

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DonchianWidth(Strategy):
    """Donchian Width Volatility Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "DC_004"
        self.strategy_name = "Donchian Width"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'width_lookback', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'width_threshold', 'type': float, 'min': 0.5, 'max': 1.0, 'default': 0.7},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _donchian(self, candles=None):
        """Calculate Donchian Channel"""
        if candles is None:
            candles = self.candles

        high = candles[:, 3]
        low = candles[:, 4]
        period = self.hp['period']

        upper = np.max(high[-period:])
        lower = np.min(low[-period:])
        middle = (upper + lower) / 2
        width = upper - lower

        return upper, middle, lower, width

    @property
    def upper(self) -> float:
        upper, _, _, _ = self._donchian()
        return upper

    @property
    def lower(self) -> float:
        _, _, lower, _ = self._donchian()
        return lower

    @property
    def width(self) -> float:
        _, _, _, width = self._donchian()
        return width

    @property
    def width_percentile(self) -> float:
        """Calculate where current width ranks vs recent history"""
        lookback = self.hp['width_lookback']
        widths = []

        for i in range(lookback):
            idx = -(i + 1)
            candles = self.candles[:idx] if idx < -1 else self.candles
            if len(candles) < self.hp['period']:
                break
            _, _, _, w = self._donchian(candles)
            widths.append(w)

        if len(widths) < 2:
            return 0.5

        widths = np.array(widths)
        current_width = self.width
        percentile = np.sum(widths < current_width) / len(widths)
        return percentile

    @property
    def width_expanding(self) -> bool:
        """Check if width is expanding (above threshold percentile)"""
        return self.width_percentile > self.hp['width_threshold']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.close > self.upper and self.width_expanding

    def should_short(self) -> bool:
        return self.close < self.lower and self.width_expanding

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
        # Exit when width contracts
        if self.is_long and not self.width_expanding:
            if self.close < self.lower:
                self.liquidate()
        elif self.is_short and not self.width_expanding:
            if self.close > self.upper:
                self.liquidate()
