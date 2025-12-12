"""
ADV_005: Gann Method Strategy
-----------------------------
Simplified Gann analysis using price/time relationships.

Entry Long: Price at Gann support angle
Entry Short: Price at Gann resistance angle

Optimal Timeframes: 4h, 1d
Complexity: 7/10
Crypto Suitability: 6/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class GannMethod(Strategy):
    """Gann Method Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_005"
        self.strategy_name = "Gann Method"
        self.complexity = 7
        self.crypto_suitability = 6

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 80, 'default': 50},
            {'name': 'angle_tolerance', 'type': float, 'min': 0.5, 'max': 2.0, 'default': 1.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_gann_levels(self) -> dict:
        """Calculate Gann support/resistance levels"""
        lookback = self.hp['lookback']

        # Find significant high and low
        sig_high = np.max(self.candles[-lookback:, 3])
        sig_low = np.min(self.candles[-lookback:, 4])

        # Gann levels based on square of 9 concept (simplified)
        range_size = sig_high - sig_low

        # Key Gann angles: 1x1 (45°), 2x1 (63.75°), 1x2 (26.25°)
        levels = {
            'high': sig_high,
            'low': sig_low,
            '1x1_up': sig_low + range_size * 0.5,
            '2x1_up': sig_low + range_size * 0.25,
            '1x2_up': sig_low + range_size * 0.75,
            '1x1_down': sig_high - range_size * 0.5,
            '2x1_down': sig_high - range_size * 0.75,
            '1x2_down': sig_high - range_size * 0.25,
        }

        return levels

    def _is_at_support(self) -> bool:
        """Check if price is at Gann support"""
        levels = self._calculate_gann_levels()
        tolerance = self.atr * self.hp['angle_tolerance']

        support_levels = [levels['low'], levels['2x1_up'], levels['1x1_up']]

        for level in support_levels:
            if abs(self.low - level) < tolerance:
                return True
        return False

    def _is_at_resistance(self) -> bool:
        """Check if price is at Gann resistance"""
        levels = self._calculate_gann_levels()
        tolerance = self.atr * self.hp['angle_tolerance']

        resistance_levels = [levels['high'], levels['1x2_down'], levels['1x1_down']]

        for level in resistance_levels:
            if abs(self.high - level) < tolerance:
                return True
        return False

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def trend(self) -> int:
        ma = ta.sma(self.candles, period=20)
        if self.close > ma:
            return 1
        elif self.close < ma:
            return -1
        return 0

    def should_long(self) -> bool:
        at_support = self._is_at_support()
        bullish_candle = self.close > self.open
        uptrend = self.trend == 1

        return at_support and bullish_candle and uptrend

    def should_short(self) -> bool:
        at_resistance = self._is_at_resistance()
        bearish_candle = self.close < self.open
        downtrend = self.trend == -1

        return at_resistance and bearish_candle and downtrend

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()
