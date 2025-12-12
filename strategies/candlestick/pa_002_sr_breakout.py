"""
PA_002: Support/Resistance Breakout Strategy
--------------------------------------------
Trade breakouts through key support and resistance levels.

Entry Long: Price breaks above resistance
Entry Short: Price breaks below support

Optimal Timeframes: 15m, 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SRBreakout(Strategy):
    """Support/Resistance Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PA_002"
        self.strategy_name = "SR Breakout"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'sr_lookback', 'type': int, 'min': 20, 'max': 100, 'default': 50},
            {'name': 'min_touches', 'type': int, 'min': 2, 'max': 5, 'default': 2},
            {'name': 'breakout_confirm', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _find_key_resistance(self) -> float:
        """Find most significant resistance level"""
        lookback = self.hp['sr_lookback']
        highs = self.candles[-lookback:, 3]

        # Find swing highs
        swing_highs = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swing_highs.append(highs[i])

        if not swing_highs:
            return float('inf')

        # Return highest recent resistance
        return max(swing_highs[-3:]) if len(swing_highs) >= 3 else max(swing_highs)

    def _find_key_support(self) -> float:
        """Find most significant support level"""
        lookback = self.hp['sr_lookback']
        lows = self.candles[-lookback:, 4]

        # Find swing lows
        swing_lows = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swing_lows.append(lows[i])

        if not swing_lows:
            return 0

        # Return lowest recent support
        return min(swing_lows[-3:]) if len(swing_lows) >= 3 else min(swing_lows)

    def _broke_resistance(self) -> bool:
        """Check if price broke above resistance"""
        resistance = self._find_key_resistance()
        confirm = self.close * self.hp['breakout_confirm']

        # Previous close below, current close above with confirmation
        prev_close = self.candles[-2, 2]
        return prev_close < resistance and self.close > resistance + confirm

    def _broke_support(self) -> bool:
        """Check if price broke below support"""
        support = self._find_key_support()
        confirm = self.close * self.hp['breakout_confirm']

        # Previous close above, current close below with confirmation
        prev_close = self.candles[-2, 2]
        return prev_close > support and self.close < support - confirm

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._broke_resistance()

    def should_short(self) -> bool:
        return self._broke_support()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        resistance = self._find_key_resistance()
        stop = max(resistance - (self.atr * self.hp['atr_multiplier_sl']),
                   entry - (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        support = self._find_key_support()
        stop = min(support + (self.atr * self.hp['atr_multiplier_sl']),
                   entry + (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
