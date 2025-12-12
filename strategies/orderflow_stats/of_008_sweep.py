"""
OF_008: Sweep Detector Strategy
-------------------------------
Detect and trade sweep patterns.

Entry Long: Low sweep and reversal
Entry Short: High sweep and reversal

Optimal Timeframes: 5m, 15m
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SweepDetector(Strategy):
    """Sweep Detector Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "OF_008"
        self.strategy_name = "Sweep Detector"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'sweep_depth', 'type': float, 'min': 0.1, 'max': 0.5, 'default': 0.2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _detect_low_sweep(self) -> bool:
        """Detect sweep of lows and reversal"""
        lookback = self.hp['lookback']

        # Find significant low
        recent_lows = self.candles[-lookback:-2, 4]
        sig_low = np.min(recent_lows)

        # Previous candle swept the low
        prev_low = self.candles[-2, 4]
        swept = prev_low < sig_low

        # Current candle reverses
        curr_bullish = self.close > self.open
        curr_close_above = self.close > sig_low

        # RSI confirmation
        rsi = ta.rsi(self.candles, period=14)
        oversold_area = rsi < 45

        return swept and curr_bullish and curr_close_above and oversold_area

    def _detect_high_sweep(self) -> bool:
        """Detect sweep of highs and reversal"""
        lookback = self.hp['lookback']

        # Find significant high
        recent_highs = self.candles[-lookback:-2, 3]
        sig_high = np.max(recent_highs)

        # Previous candle swept the high
        prev_high = self.candles[-2, 3]
        swept = prev_high > sig_high

        # Current candle reverses
        curr_bearish = self.close < self.open
        curr_close_below = self.close < sig_high

        # RSI confirmation
        rsi = ta.rsi(self.candles, period=14)
        overbought_area = rsi > 55

        return swept and curr_bearish and curr_close_below and overbought_area

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._detect_low_sweep()

    def should_short(self) -> bool:
        return self._detect_high_sweep()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        # Stop below the sweep low
        sweep_low = min(self.candles[-2, 4], self.low)
        stop = sweep_low - (self.atr * 0.3)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        # Stop above the sweep high
        sweep_high = max(self.candles[-2, 3], self.high)
        stop = sweep_high + (self.atr * 0.3)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        rsi = ta.rsi(self.candles, period=14)
        if self.is_long and rsi > 60:
            self.liquidate()
        elif self.is_short and rsi < 40:
            self.liquidate()
