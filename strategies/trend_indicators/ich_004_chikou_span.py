"""
ICH_004: Ichimoku Chikou Span Strategy
--------------------------------------
Chikou Span (Lagging Span) confirmation signals.
Chikou above past price = bullish.
Chikou below past price = bearish.

Entry Long: Chikou crosses above past price
Entry Short: Chikou crosses below past price

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class IchimokuChikouSpan(Strategy):
    """Ichimoku Chikou Span Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ICH_004"
        self.strategy_name = "Ichimoku Chikou Span"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'displacement', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    @property
    def chikou(self) -> float:
        """Current close (will be plotted 26 periods back)"""
        return self.close

    @property
    def chikou_prev(self) -> float:
        """Previous close"""
        return self.candles[-2, 2]

    @property
    def past_price(self) -> float:
        """Price 26 periods ago (where Chikou is plotted)"""
        displacement = self.hp['displacement']
        if len(self.candles) > displacement:
            return self.candles[-displacement, 2]
        return self.close

    @property
    def past_price_prev(self) -> float:
        """Previous past price for crossover detection"""
        displacement = self.hp['displacement']
        if len(self.candles) > displacement + 1:
            return self.candles[-displacement - 1, 2]
        return self.candles[-2, 2]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def chikou_above_price(self) -> bool:
        return self.chikou > self.past_price

    @property
    def chikou_below_price(self) -> bool:
        return self.chikou < self.past_price

    @property
    def chikou_crossed_above(self) -> bool:
        return self.chikou_prev <= self.past_price_prev and self.chikou > self.past_price

    @property
    def chikou_crossed_below(self) -> bool:
        return self.chikou_prev >= self.past_price_prev and self.chikou < self.past_price

    def should_long(self) -> bool:
        return self.chikou_crossed_above

    def should_short(self) -> bool:
        return self.chikou_crossed_below

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
        if self.is_long and self.chikou_below_price:
            self.liquidate()
        elif self.is_short and self.chikou_above_price:
            self.liquidate()
