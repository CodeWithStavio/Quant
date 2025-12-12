"""
ADV_007: Smart Money Concepts Strategy
--------------------------------------
Trade using SMC/ICT concepts.

Entry Long: Bullish break of structure + order block
Entry Short: Bearish break of structure + order block

Optimal Timeframes: 15m, 1h
Complexity: 8/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SmartMoneyConcept(Strategy):
    """Smart Money Concepts Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_007"
        self.strategy_name = "Smart Money Concept"
        self.complexity = 8
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _find_bos(self) -> dict:
        """Find Break of Structure"""
        lookback = self.hp['lookback']

        # Find swing highs and lows
        swing_high = np.max(self.candles[-lookback:-5, 3])
        swing_low = np.min(self.candles[-lookback:-5, 4])

        # Check for BOS
        bullish_bos = self.close > swing_high
        bearish_bos = self.close < swing_low

        return {
            'bullish_bos': bullish_bos,
            'bearish_bos': bearish_bos,
            'swing_high': swing_high,
            'swing_low': swing_low
        }

    def _find_order_block(self, direction: str) -> float:
        """Find potential order block"""
        lookback = 15

        if direction == 'bullish':
            # Bullish OB: Last bearish candle before up move
            for i in range(5, lookback):
                # Bearish candle
                if self.candles[-i, 2] < self.candles[-i, 1]:
                    # Followed by bullish move
                    subsequent_high = np.max(self.candles[-i+1:-1, 3])
                    if subsequent_high > self.candles[-i, 3]:
                        return self.candles[-i, 4]  # OB low
            return None

        else:
            # Bearish OB: Last bullish candle before down move
            for i in range(5, lookback):
                # Bullish candle
                if self.candles[-i, 2] > self.candles[-i, 1]:
                    # Followed by bearish move
                    subsequent_low = np.min(self.candles[-i+1:-1, 4])
                    if subsequent_low < self.candles[-i, 4]:
                        return self.candles[-i, 3]  # OB high
            return None

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        bos = self._find_bos()
        if not bos['bullish_bos']:
            return False

        # Look for retest of order block
        ob_level = self._find_order_block('bullish')
        if ob_level is None:
            return False

        # Price retesting OB
        near_ob = self.low <= ob_level * 1.01
        bullish_candle = self.close > self.open

        return near_ob and bullish_candle

    def should_short(self) -> bool:
        bos = self._find_bos()
        if not bos['bearish_bos']:
            return False

        # Look for retest of order block
        ob_level = self._find_order_block('bearish')
        if ob_level is None:
            return False

        # Price retesting OB
        near_ob = self.high >= ob_level * 0.99
        bearish_candle = self.close < self.open

        return near_ob and bearish_candle

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        ob_level = self._find_order_block('bullish')
        stop = ob_level - (self.atr * 0.5) if ob_level else entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        ob_level = self._find_order_block('bearish')
        stop = ob_level + (self.atr * 0.5) if ob_level else entry + (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Trail with ATR
        if self.is_long:
            trail = self.close - (self.atr * 1.5)
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short:
            trail = self.close + (self.atr * 1.5)
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail
