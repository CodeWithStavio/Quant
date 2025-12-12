"""
BB_001: Bollinger Band Bounce Strategy
--------------------------------------
Mean reversion at Bollinger Band extremes.

Entry Long: Price touches lower band and reverses
Entry Short: Price touches upper band and reverses

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BBBounce(Strategy):
    """Bollinger Band Bounce Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BB_001"
        self.strategy_name = "BB Bounce"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'std_dev', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'require_reversal', 'type': bool, 'default': True},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 0.5, 'max': 2.0, 'default': 1.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
        ]

    def _get_bb(self, candles=None):
        if candles is None:
            candles = self.candles
        return ta.bollinger_bands(
            candles,
            period=self.hp['period'],
            devup=self.hp['std_dev'],
            devdn=self.hp['std_dev']
        )

    @property
    def bb_upper(self) -> float:
        upper, middle, lower = self._get_bb()
        return upper

    @property
    def bb_middle(self) -> float:
        upper, middle, lower = self._get_bb()
        return middle

    @property
    def bb_lower(self) -> float:
        upper, middle, lower = self._get_bb()
        return lower

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _at_lower_band(self) -> bool:
        return self.low <= self.bb_lower

    def _at_upper_band(self) -> bool:
        return self.high >= self.bb_upper

    def _bullish_reversal(self) -> bool:
        if not self.hp.get('require_reversal', True):
            return True
        # Current candle is bullish
        bullish = self.close > self.open
        # Lower wick shows rejection
        body = abs(self.close - self.open)
        lower_wick = min(self.open, self.close) - self.low
        return bullish and lower_wick > body * 0.5

    def _bearish_reversal(self) -> bool:
        if not self.hp.get('require_reversal', True):
            return True
        # Current candle is bearish
        bearish = self.close < self.open
        # Upper wick shows rejection
        body = abs(self.close - self.open)
        upper_wick = self.high - max(self.open, self.close)
        return bearish and upper_wick > body * 0.5

    def should_long(self) -> bool:
        return self._at_lower_band() and self._bullish_reversal()

    def should_short(self) -> bool:
        return self._at_upper_band() and self._bearish_reversal()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.bb_lower - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.6, self.bb_middle),
            (0.4, self.bb_upper),
        ]

    def go_short(self):
        entry = self.price
        stop = self.bb_upper + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.6, self.bb_middle),
            (0.4, self.bb_lower),
        ]

    def update_position(self):
        pass
