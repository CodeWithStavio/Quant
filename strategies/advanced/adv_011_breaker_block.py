"""
ADV_011: Breaker Block Strategy
-------------------------------
Trade based on breaker block detection (failed order blocks).

Entry Long: Bullish breaker block retest
Entry Short: Bearish breaker block retest

Optimal Timeframes: 15m, 1h
Complexity: 8/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BreakerBlock(Strategy):
    """Breaker Block Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_011"
        self.strategy_name = "Breaker Block"
        self.complexity = 8
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 40, 'default': 25},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _find_bullish_breaker(self) -> dict:
        """
        Find bullish breaker (bearish OB that got broken through and flipped)
        Pattern: Up move -> down candle (bearish OB) -> price breaks below -> recovers above
        """
        lookback = self.hp['lookback']

        for i in range(5, lookback):
            # Find bearish OB that was violated
            if self.candles[-i, 2] > self.candles[-i, 1]:  # Up candle (potential failed bearish OB)
                ob_low = self.candles[-i, 4]
                ob_high = self.candles[-i, 3]

                # Check if price went below then recovered above
                price_below = np.min(self.candles[-i+1:-3, 4]) < ob_low
                price_above = self.candles[-2, 2] > ob_high or self.candles[-1, 2] > ob_high

                if price_below and price_above:
                    return {
                        'high': ob_high,
                        'low': ob_low,
                        'found': True
                    }

        return {'found': False}

    def _find_bearish_breaker(self) -> dict:
        """
        Find bearish breaker (bullish OB that got broken through and flipped)
        """
        lookback = self.hp['lookback']

        for i in range(5, lookback):
            # Find bullish OB that was violated
            if self.candles[-i, 2] < self.candles[-i, 1]:  # Down candle (potential failed bullish OB)
                ob_low = self.candles[-i, 4]
                ob_high = self.candles[-i, 3]

                # Check if price went above then dropped below
                price_above = np.max(self.candles[-i+1:-3, 3]) > ob_high
                price_below = self.candles[-2, 2] < ob_low or self.candles[-1, 2] < ob_low

                if price_above and price_below:
                    return {
                        'high': ob_high,
                        'low': ob_low,
                        'found': True
                    }

        return {'found': False}

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        breaker = self._find_bullish_breaker()
        if not breaker['found']:
            return False

        # Price retesting breaker from above
        retest = self.low <= breaker['high'] and self.close >= breaker['low']
        bullish = self.close > self.open

        return retest and bullish

    def should_short(self) -> bool:
        breaker = self._find_bearish_breaker()
        if not breaker['found']:
            return False

        # Price retesting breaker from below
        retest = self.high >= breaker['low'] and self.close <= breaker['high']
        bearish = self.close < self.open

        return retest and bearish

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        breaker = self._find_bullish_breaker()
        stop = breaker['low'] - (self.atr * 0.3) if breaker['found'] else entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        breaker = self._find_bearish_breaker()
        stop = breaker['high'] + (self.atr * 0.3) if breaker['found'] else entry + (self.atr * 2)
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
