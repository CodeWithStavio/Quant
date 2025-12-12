"""
ATR_004: Chandelier Exit Strategy
---------------------------------
Charles Le Beau's Chandelier Exit for trend following.
Trailing stop from highest high (long) or lowest low (short).

Entry: Trend reversal when price crosses chandelier
Exit: Price touches chandelier exit

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ChandelierExit(Strategy):
    """Chandelier Exit Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ATR_004"
        self.strategy_name = "Chandelier Exit"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 25, 'default': 22},
            {'name': 'atr_period', 'type': int, 'min': 14, 'max': 22, 'default': 22},
            {'name': 'multiplier', 'type': float, 'min': 2.5, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    @property
    def highest_high(self) -> float:
        return np.max(self.candles[-self.hp['period']:, 3])

    @property
    def lowest_low(self) -> float:
        return np.min(self.candles[-self.hp['period']:, 4])

    @property
    def chandelier_long(self) -> float:
        """Long exit: highest high - ATR * multiplier"""
        return self.highest_high - (self.atr * self.hp['multiplier'])

    @property
    def chandelier_short(self) -> float:
        """Short exit: lowest low + ATR * multiplier"""
        return self.lowest_low + (self.atr * self.hp['multiplier'])

    @property
    def chandelier_long_prev(self) -> float:
        """Previous bar chandelier long"""
        candles = self.candles[:-1]
        period = self.hp['period']
        highest = np.max(candles[-period:, 3])
        atr_prev = ta.atr(candles, period=self.hp['atr_period'])
        return highest - (atr_prev * self.hp['multiplier'])

    @property
    def chandelier_short_prev(self) -> float:
        """Previous bar chandelier short"""
        candles = self.candles[:-1]
        period = self.hp['period']
        lowest = np.min(candles[-period:, 4])
        atr_prev = ta.atr(candles, period=self.hp['atr_period'])
        return lowest + (atr_prev * self.hp['multiplier'])

    def _trend_bullish(self) -> bool:
        """Price above long chandelier"""
        return self.close > self.chandelier_long

    def _trend_bearish(self) -> bool:
        """Price below short chandelier"""
        return self.close < self.chandelier_short

    def should_long(self) -> bool:
        # Bullish reversal: price crosses above long chandelier from below
        prev_close = self.candles[-2, 2]
        return prev_close <= self.chandelier_long_prev and self.close > self.chandelier_long

    def should_short(self) -> bool:
        # Bearish reversal: price crosses below short chandelier from above
        prev_close = self.candles[-2, 2]
        return prev_close >= self.chandelier_short_prev and self.close < self.chandelier_short

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.chandelier_long
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.chandelier_short
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Update trailing stop using chandelier
        if self.is_long:
            new_stop = self.chandelier_long
            if new_stop > self.position.entry_price - (self.atr * self.hp['multiplier']):
                self.stop_loss = self.position.qty, new_stop

            if self.low <= self.chandelier_long:
                self.liquidate()

        elif self.is_short:
            new_stop = self.chandelier_short
            if new_stop < self.position.entry_price + (self.atr * self.hp['multiplier']):
                self.stop_loss = self.position.qty, new_stop

            if self.high >= self.chandelier_short:
                self.liquidate()
