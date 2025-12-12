"""
BB_007: BB Walking the Bands Strategy
-------------------------------------
Trend following when price consistently touches upper/lower band.

Entry Long: Price consistently touching upper band (strong uptrend)
Entry Short: Price consistently touching lower band (strong downtrend)

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BBWalking(Strategy):
    """BB Walking the Bands Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BB_007"
        self.strategy_name = "BB Walking"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'std_dev', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'walk_bars', 'type': int, 'min': 3, 'max': 7, 'default': 4},
            {'name': 'touch_threshold', 'type': float, 'min': 0.01, 'max': 0.05, 'default': 0.02},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 3.0, 'max': 6.0, 'default': 4.0},
        ]

    def _get_bb_sequential(self):
        return ta.bollinger_bands(
            self.candles,
            period=self.hp['period'],
            devup=self.hp['std_dev'],
            devdn=self.hp['std_dev'],
            sequential=True
        )

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _walking_upper(self) -> bool:
        """Check if price has been consistently near upper band"""
        upper, middle, lower = self._get_bb_sequential()
        bars = self.hp['walk_bars']
        threshold = self.hp['touch_threshold']

        touches = 0
        for i in range(1, bars + 1):
            high = self.candles[-i, 3]
            band_dist = abs(high - upper[-i]) / upper[-i]
            if band_dist < threshold or high >= upper[-i]:
                touches += 1

        return touches >= bars - 1

    def _walking_lower(self) -> bool:
        """Check if price has been consistently near lower band"""
        upper, middle, lower = self._get_bb_sequential()
        bars = self.hp['walk_bars']
        threshold = self.hp['touch_threshold']

        touches = 0
        for i in range(1, bars + 1):
            low = self.candles[-i, 4]
            band_dist = abs(low - lower[-i]) / lower[-i]
            if band_dist < threshold or low <= lower[-i]:
                touches += 1

        return touches >= bars - 1

    def _pullback_to_middle(self) -> bool:
        """Price pulled back toward middle band"""
        upper, middle, lower = self._get_bb_sequential()
        # Close is between middle and upper band
        return middle[-1] < self.close < upper[-1]

    def _rally_to_middle(self) -> bool:
        """Price rallied toward middle band"""
        upper, middle, lower = self._get_bb_sequential()
        # Close is between lower and middle band
        return lower[-1] < self.close < middle[-1]

    def should_long(self) -> bool:
        # Walking upper band, pullback to middle, continue trend
        return self._walking_upper() and self._pullback_to_middle() and self.close > self.open

    def should_short(self) -> bool:
        # Walking lower band, rally to middle, continue trend
        return self._walking_lower() and self._rally_to_middle() and self.close < self.open

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        upper, middle, lower = self._get_bb_sequential()
        stop = middle[-1] - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        upper, middle, lower = self._get_bb_sequential()
        stop = middle[-1] + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        upper, middle, lower = self._get_bb_sequential()
        if self.is_long and self.close < middle[-1]:
            self.liquidate()
        elif self.is_short and self.close > middle[-1]:
            self.liquidate()
