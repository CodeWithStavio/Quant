"""
ADV_002: Market Structure Strategy
----------------------------------
Trade based on market structure (HH, HL, LH, LL).

Entry Long: Higher high/higher low structure
Entry Short: Lower high/lower low structure

Optimal Timeframes: 1h, 4h
Complexity: 7/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MarketStructure(Strategy):
    """Market Structure Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_002"
        self.strategy_name = "Market Structure"
        self.complexity = 7
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'swing_lookback', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _find_swing_points(self) -> dict:
        """Find recent swing highs and lows"""
        lookback = self.hp['swing_lookback']

        swing_highs = []
        swing_lows = []

        for i in range(5, lookback * 2):
            if i + 3 >= len(self.candles):
                continue

            # Swing high: higher than 2 bars before and after
            is_swing_high = (
                self.candles[-i, 3] > self.candles[-i-1, 3] and
                self.candles[-i, 3] > self.candles[-i-2, 3] and
                self.candles[-i, 3] > self.candles[-i+1, 3] and
                self.candles[-i, 3] > self.candles[-i+2, 3]
            )

            # Swing low: lower than 2 bars before and after
            is_swing_low = (
                self.candles[-i, 4] < self.candles[-i-1, 4] and
                self.candles[-i, 4] < self.candles[-i-2, 4] and
                self.candles[-i, 4] < self.candles[-i+1, 4] and
                self.candles[-i, 4] < self.candles[-i+2, 4]
            )

            if is_swing_high:
                swing_highs.append(self.candles[-i, 3])
            if is_swing_low:
                swing_lows.append(self.candles[-i, 4])

            if len(swing_highs) >= 2 and len(swing_lows) >= 2:
                break

        return {'highs': swing_highs, 'lows': swing_lows}

    def _detect_structure(self) -> str:
        """Detect market structure"""
        swings = self._find_swing_points()

        if len(swings['highs']) < 2 or len(swings['lows']) < 2:
            return 'undefined'

        # Most recent swing first
        hh = swings['highs'][0] > swings['highs'][1]  # Higher high
        hl = swings['lows'][0] > swings['lows'][1]    # Higher low
        lh = swings['highs'][0] < swings['highs'][1]  # Lower high
        ll = swings['lows'][0] < swings['lows'][1]    # Lower low

        if hh and hl:
            return 'bullish'
        elif lh and ll:
            return 'bearish'
        elif hh and ll:
            return 'expansion'
        elif lh and hl:
            return 'consolidation'

        return 'undefined'

    @property
    def structure(self) -> str:
        return self._detect_structure()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    def should_long(self) -> bool:
        return self.structure == 'bullish' and self.rsi < 65

    def should_short(self) -> bool:
        return self.structure == 'bearish' and self.rsi > 35

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        swings = self._find_swing_points()
        stop = swings['lows'][0] - (self.atr * 0.5) if swings['lows'] else entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        swings = self._find_swing_points()
        stop = swings['highs'][0] + (self.atr * 0.5) if swings['highs'] else entry + (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        structure = self.structure
        if self.is_long and structure == 'bearish':
            self.liquidate()
        elif self.is_short and structure == 'bullish':
            self.liquidate()
