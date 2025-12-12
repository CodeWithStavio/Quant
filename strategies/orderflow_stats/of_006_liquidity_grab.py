"""
OF_006: Liquidity Grab Strategy
-------------------------------
Trade liquidity grab patterns (stop hunts).

Entry Long: Liquidity grab below support then reversal
Entry Short: Liquidity grab above resistance then reversal

Optimal Timeframes: 5m, 15m
Complexity: 7/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class LiquidityGrab(Strategy):
    """Liquidity Grab Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "OF_006"
        self.strategy_name = "Liquidity Grab"
        self.complexity = 7
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'wick_ratio', 'type': float, 'min': 0.5, 'max': 0.8, 'default': 0.6},
            {'name': 'volume_spike', 'type': float, 'min': 1.3, 'max': 2.5, 'default': 1.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _is_liquidity_grab_low(self) -> bool:
        """Detect liquidity grab below support"""
        lookback = self.hp['lookback']

        # Find recent support level
        recent_lows = self.candles[-lookback:-1, 4]
        support = np.min(recent_lows)

        # Current candle broke below support
        broke_support = self.low < support

        # But closed above support (grab and reversal)
        closed_above = self.close > support

        # Long lower wick (rejection)
        candle_range = self.high - self.low
        if candle_range == 0:
            return False
        lower_wick = min(self.open, self.close) - self.low
        wick_ratio = lower_wick / candle_range
        long_lower_wick = wick_ratio > self.hp['wick_ratio']

        # Volume spike
        avg_vol = np.mean(self.candles[-lookback:-1, 5])
        high_volume = self.candles[-1, 5] > avg_vol * self.hp['volume_spike']

        return broke_support and closed_above and long_lower_wick and high_volume

    def _is_liquidity_grab_high(self) -> bool:
        """Detect liquidity grab above resistance"""
        lookback = self.hp['lookback']

        # Find recent resistance level
        recent_highs = self.candles[-lookback:-1, 3]
        resistance = np.max(recent_highs)

        # Current candle broke above resistance
        broke_resistance = self.high > resistance

        # But closed below resistance (grab and reversal)
        closed_below = self.close < resistance

        # Long upper wick (rejection)
        candle_range = self.high - self.low
        if candle_range == 0:
            return False
        upper_wick = self.high - max(self.open, self.close)
        wick_ratio = upper_wick / candle_range
        long_upper_wick = wick_ratio > self.hp['wick_ratio']

        # Volume spike
        avg_vol = np.mean(self.candles[-lookback:-1, 5])
        high_volume = self.candles[-1, 5] > avg_vol * self.hp['volume_spike']

        return broke_resistance and closed_below and long_upper_wick and high_volume

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_liquidity_grab_low()

    def should_short(self) -> bool:
        return self._is_liquidity_grab_high()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.low - (self.atr * 0.5)  # Below the grab
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.high + (self.atr * 0.5)  # Above the grab
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Trail with ATR
        if self.is_long:
            trail = self.close - self.atr
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short:
            trail = self.close + self.atr
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail
