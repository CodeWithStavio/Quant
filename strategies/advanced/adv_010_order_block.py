"""
ADV_010: Order Block Strategy
-----------------------------
Trade based on order block detection and retest.

Entry Long: Retest of bullish order block
Entry Short: Retest of bearish order block

Optimal Timeframes: 15m, 1h
Complexity: 7/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class OrderBlock(Strategy):
    """Order Block Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_010"
        self.strategy_name = "Order Block"
        self.complexity = 7
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _find_bullish_ob(self) -> dict:
        """Find bullish order block (last down candle before up move)"""
        lookback = self.hp['lookback']

        for i in range(3, lookback):
            # Down candle
            if self.candles[-i, 2] < self.candles[-i, 1]:
                # Followed by significant up move
                up_move = self.candles[-i+1, 3] > self.candles[-i, 3]
                broke_high = np.max(self.candles[-i+1:-1, 3]) > self.candles[-i, 3]

                if up_move and broke_high:
                    return {
                        'high': self.candles[-i, 3],
                        'low': self.candles[-i, 4],
                        'found': True
                    }

        return {'found': False}

    def _find_bearish_ob(self) -> dict:
        """Find bearish order block (last up candle before down move)"""
        lookback = self.hp['lookback']

        for i in range(3, lookback):
            # Up candle
            if self.candles[-i, 2] > self.candles[-i, 1]:
                # Followed by significant down move
                down_move = self.candles[-i+1, 4] < self.candles[-i, 4]
                broke_low = np.min(self.candles[-i+1:-1, 4]) < self.candles[-i, 4]

                if down_move and broke_low:
                    return {
                        'high': self.candles[-i, 3],
                        'low': self.candles[-i, 4],
                        'found': True
                    }

        return {'found': False}

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        ob = self._find_bullish_ob()
        if not ob['found']:
            return False

        # Price retesting OB zone
        retest = self.low <= ob['high'] and self.close >= ob['low']
        bullish = self.close > self.open

        return retest and bullish

    def should_short(self) -> bool:
        ob = self._find_bearish_ob()
        if not ob['found']:
            return False

        # Price retesting OB zone
        retest = self.high >= ob['low'] and self.close <= ob['high']
        bearish = self.close < self.open

        return retest and bearish

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        ob = self._find_bullish_ob()
        stop = ob['low'] - (self.atr * 0.3) if ob['found'] else entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        ob = self._find_bearish_ob()
        stop = ob['high'] + (self.atr * 0.3) if ob['found'] else entry + (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long:
            trail = self.close - self.atr
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short:
            trail = self.close + self.atr
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail
