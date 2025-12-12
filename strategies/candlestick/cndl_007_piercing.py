"""
CNDL_007: Piercing/Dark Cloud Strategy
--------------------------------------
Piercing Line = bullish reversal (close above 50% of prev body).
Dark Cloud Cover = bearish reversal (close below 50% of prev body).

Entry: Trade the reversal signal

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class PiercingDarkCloud(Strategy):
    """Piercing/Dark Cloud Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_007"
        self.strategy_name = "Piercing Dark Cloud"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'penetration_min', 'type': float, 'min': 0.4, 'max': 0.6, 'default': 0.5},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _is_piercing_line(self) -> bool:
        """Check for piercing line pattern (bullish)"""
        # Previous candle (bearish)
        prev_open = self.candles[-2, 1]
        prev_close = self.candles[-2, 2]
        prev_body = prev_open - prev_close  # Bearish so open > close

        if prev_body <= 0:  # Not bearish
            return False

        # Current candle (bullish)
        curr_open = self.open
        curr_close = self.close

        if curr_close <= curr_open:  # Not bullish
            return False

        # Opens below previous low
        prev_low = self.candles[-2, 4]
        if curr_open > prev_low:
            return False

        # Closes above midpoint of previous body
        midpoint = prev_close + (prev_body * self.hp['penetration_min'])
        return curr_close > midpoint and curr_close < prev_open

    def _is_dark_cloud(self) -> bool:
        """Check for dark cloud cover pattern (bearish)"""
        # Previous candle (bullish)
        prev_open = self.candles[-2, 1]
        prev_close = self.candles[-2, 2]
        prev_body = prev_close - prev_open  # Bullish so close > open

        if prev_body <= 0:  # Not bullish
            return False

        # Current candle (bearish)
        curr_open = self.open
        curr_close = self.close

        if curr_close >= curr_open:  # Not bearish
            return False

        # Opens above previous high
        prev_high = self.candles[-2, 3]
        if curr_open < prev_high:
            return False

        # Closes below midpoint of previous body
        midpoint = prev_close - (prev_body * self.hp['penetration_min'])
        return curr_close < midpoint and curr_close > prev_open

    def _in_downtrend(self) -> bool:
        ma = ta.sma(self.candles, period=self.hp['trend_period'])
        return self.close < ma

    def _in_uptrend(self) -> bool:
        ma = ta.sma(self.candles, period=self.hp['trend_period'])
        return self.close > ma

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_piercing_line() and self._in_downtrend()

    def should_short(self) -> bool:
        return self._is_dark_cloud() and self._in_uptrend()

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
        pass
