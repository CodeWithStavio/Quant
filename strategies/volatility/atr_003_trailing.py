"""
ATR_003: ATR Trailing Stop Strategy
-----------------------------------
Dynamic trailing stop based on ATR distance from highest/lowest.

Entry: Trend following with ATR trailing stop
Exit: Price touches trailing stop

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ATRTrailingStop(Strategy):
    """ATR Trailing Stop Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ATR_003"
        self.strategy_name = "ATR Trailing Stop"
        self.complexity = 3
        self.crypto_suitability = 8
        self._trailing_stop = None
        self._highest = None
        self._lowest = None

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'atr_period', 'type': int, 'min': 10, 'max': 21, 'default': 14},
            {'name': 'atr_multiplier', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 50, 'default': 20},
            {'name': 'trend_filter', 'type': bool, 'default': True},
        ]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    @property
    def ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ma_period'])

    def _calculate_atr_stop(self):
        """Calculate ATR-based trailing stop levels"""
        atr_val = self.atr
        mult = self.hp['atr_multiplier']

        long_stop = self.close - (atr_val * mult)
        short_stop = self.close + (atr_val * mult)

        return long_stop, short_stop

    @property
    def trend_up(self) -> bool:
        if self.hp['trend_filter']:
            return self.close > self.ma
        return True

    @property
    def trend_down(self) -> bool:
        if self.hp['trend_filter']:
            return self.close < self.ma
        return True

    def should_long(self) -> bool:
        # Long when price is above MA and rising above ATR stop
        long_stop, _ = self._calculate_atr_stop()
        prev_close = self.candles[-2, 2]

        # Look for bullish signal: price moving up from below stop
        return self.trend_up and prev_close <= long_stop and self.close > long_stop

    def should_short(self) -> bool:
        # Short when price is below MA and falling below ATR stop
        _, short_stop = self._calculate_atr_stop()
        prev_close = self.candles[-2, 2]

        return self.trend_down and prev_close >= short_stop and self.close < short_stop

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        long_stop, _ = self._calculate_atr_stop()
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self._trailing_stop = long_stop
        self._highest = entry

        self.buy = qty, entry
        self.stop_loss = qty, long_stop

    def go_short(self):
        entry = self.price
        _, short_stop = self._calculate_atr_stop()
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self._trailing_stop = short_stop
        self._lowest = entry

        self.sell = qty, entry
        self.stop_loss = qty, short_stop

    def update_position(self):
        atr_val = self.atr
        mult = self.hp['atr_multiplier']

        if self.is_long:
            # Update highest and trailing stop
            if self.close > self._highest:
                self._highest = self.close
                new_stop = self._highest - (atr_val * mult)
                if new_stop > self._trailing_stop:
                    self._trailing_stop = new_stop
                    self.stop_loss = self.position.qty, self._trailing_stop

            # Exit if price hits trailing stop
            if self.low <= self._trailing_stop:
                self.liquidate()

        elif self.is_short:
            # Update lowest and trailing stop
            if self.close < self._lowest:
                self._lowest = self.close
                new_stop = self._lowest + (atr_val * mult)
                if new_stop < self._trailing_stop:
                    self._trailing_stop = new_stop
                    self.stop_loss = self.position.qty, self._trailing_stop

            # Exit if price hits trailing stop
            if self.high >= self._trailing_stop:
                self.liquidate()

    def on_close_position(self, order):
        self._trailing_stop = None
        self._highest = None
        self._lowest = None
