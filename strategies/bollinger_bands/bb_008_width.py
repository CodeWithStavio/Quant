"""
BB_008: Bollinger Band Width Strategy
-------------------------------------
Trade based on BB Width for volatility expansion/contraction.

Entry: When width crosses above threshold from low volatility state

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BBWidth(Strategy):
    """Bollinger Band Width Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BB_008"
        self.strategy_name = "BB Width"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'std_dev', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'width_lookback', 'type': int, 'min': 20, 'max': 100, 'default': 50},
            {'name': 'low_percentile', 'type': float, 'min': 0.05, 'max': 0.25, 'default': 0.1},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 3.0, 'max': 6.0, 'default': 4.0},
        ]

    def _get_bb_width(self) -> np.ndarray:
        """Calculate BB Width = (Upper - Lower) / Middle"""
        upper, middle, lower = ta.bollinger_bands(
            self.candles,
            period=self.hp['period'],
            devup=self.hp['std_dev'],
            devdn=self.hp['std_dev'],
            sequential=True
        )

        width = np.zeros(len(middle))
        for i in range(len(middle)):
            if middle[i] != 0:
                width[i] = (upper[i] - lower[i]) / middle[i]

        return width

    @property
    def width(self) -> float:
        return self._get_bb_width()[-1]

    @property
    def width_prev(self) -> float:
        return self._get_bb_width()[-2]

    @property
    def width_percentile(self) -> float:
        """Current width percentile over lookback"""
        width = self._get_bb_width()
        lookback = min(self.hp['width_lookback'], len(width))
        sorted_width = np.sort(width[-lookback:])
        percentile = np.searchsorted(sorted_width, self.width) / lookback
        return percentile

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _volatility_expanding(self) -> bool:
        """Width was low, now expanding"""
        width = self._get_bb_width()
        lookback = self.hp['width_lookback']

        # Previous width was in low percentile
        prev_low = self.width_prev <= np.percentile(width[-lookback:-1], self.hp['low_percentile'] * 100)
        # Current width is higher than previous
        expanding = self.width > self.width_prev

        return prev_low and expanding

    def _bullish_breakout(self) -> bool:
        """Price breaking upward"""
        upper, middle, lower = ta.bollinger_bands(
            self.candles,
            period=self.hp['period'],
            devup=self.hp['std_dev'],
            devdn=self.hp['std_dev']
        )
        return self.close > middle and self.close > self.candles[-2, 2]

    def _bearish_breakout(self) -> bool:
        """Price breaking downward"""
        upper, middle, lower = ta.bollinger_bands(
            self.candles,
            period=self.hp['period'],
            devup=self.hp['std_dev'],
            devdn=self.hp['std_dev']
        )
        return self.close < middle and self.close < self.candles[-2, 2]

    def should_long(self) -> bool:
        return self._volatility_expanding() and self._bullish_breakout()

    def should_short(self) -> bool:
        return self._volatility_expanding() and self._bearish_breakout()

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
        # Exit when volatility contracts again
        if self.is_long or self.is_short:
            if self.width_percentile < self.hp['low_percentile']:
                self.liquidate()
