"""
TF_007: Price Action Trend Strategy
-----------------------------------
Trade based on higher highs/lower lows structure.

Entry Long: Higher highs and higher lows pattern
Entry Short: Lower highs and lower lows pattern

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class PriceActionTrend(Strategy):
    """Price Action Trend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_007"
        self.strategy_name = "Price Action Trend"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'swing_lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.0, 'default': 3.0},
        ]

    def _find_swing_points(self) -> tuple:
        """Find recent swing highs and lows"""
        lookback = self.hp['swing_lookback']
        highs = self.candles[-lookback:, 3]
        lows = self.candles[-lookback:, 4]

        swing_highs = []
        swing_lows = []

        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append(highs[i])

            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append(lows[i])

        return swing_highs, swing_lows

    @property
    def uptrend_structure(self) -> bool:
        """Check for higher highs and higher lows"""
        swing_highs, swing_lows = self._find_swing_points()

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return False

        # Recent highs should be higher
        hh = swing_highs[-1] > swing_highs[-2]
        # Recent lows should be higher
        hl = swing_lows[-1] > swing_lows[-2]

        return hh and hl

    @property
    def downtrend_structure(self) -> bool:
        """Check for lower highs and lower lows"""
        swing_highs, swing_lows = self._find_swing_points()

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return False

        # Recent highs should be lower
        lh = swing_highs[-1] < swing_highs[-2]
        # Recent lows should be lower
        ll = swing_lows[-1] < swing_lows[-2]

        return lh and ll

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Uptrend structure with bullish candle
        return self.uptrend_structure and self.close > self.open

    def should_short(self) -> bool:
        # Downtrend structure with bearish candle
        return self.downtrend_structure and self.close < self.open

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        _, swing_lows = self._find_swing_points()
        stop = swing_lows[-1] - (self.atr * 0.5) if swing_lows else entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        swing_highs, _ = self._find_swing_points()
        stop = swing_highs[-1] + (self.atr * 0.5) if swing_highs else entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit if structure breaks
        if self.is_long and self.downtrend_structure:
            self.liquidate()
        elif self.is_short and self.uptrend_structure:
            self.liquidate()
