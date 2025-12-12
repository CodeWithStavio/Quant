"""
MA_012: MA Slope Strategy
-------------------------
Trade based on the slope/momentum of moving average.

Entry Long: MA slope positive and increasing
Entry Short: MA slope negative and decreasing

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MASlopeStrategy(Strategy):
    """MA Slope Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_012"
        self.strategy_name = "MA Slope"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 10, 'max': 50, 'default': 21},
            {'name': 'slope_lookback', 'type': int, 'min': 3, 'max': 10, 'default': 5},
            {'name': 'slope_threshold', 'type': float, 'min': 0.0001, 'max': 0.001, 'default': 0.0003},
            {'name': 'acceleration_threshold', 'type': float, 'min': 0.00001, 'max': 0.0001, 'default': 0.00005},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    @property
    def ma_sequential(self) -> np.ndarray:
        return ta.ema(self.candles, period=self.hp['ma_period'], sequential=True)

    @property
    def current_slope(self) -> float:
        """Calculate current slope of MA"""
        ma = self.ma_sequential
        lookback = self.hp['slope_lookback']
        if len(ma) < lookback:
            return 0
        return (ma[-1] - ma[-lookback]) / lookback / ma[-1]  # Normalized slope

    @property
    def prev_slope(self) -> float:
        """Calculate previous slope of MA"""
        ma = self.ma_sequential
        lookback = self.hp['slope_lookback']
        if len(ma) < lookback + 1:
            return 0
        return (ma[-2] - ma[-lookback-1]) / lookback / ma[-2]

    @property
    def slope_acceleration(self) -> float:
        """Calculate acceleration (change in slope)"""
        return self.current_slope - self.prev_slope

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _bullish_momentum(self) -> bool:
        """Check for bullish MA momentum"""
        threshold = self.hp['slope_threshold']
        accel_threshold = self.hp['acceleration_threshold']

        # Slope is positive and above threshold
        strong_slope = self.current_slope > threshold

        # Slope is increasing (positive acceleration)
        accelerating = self.slope_acceleration > accel_threshold

        # Price above MA
        price_above = self.close > self.ma_sequential[-1]

        return strong_slope and accelerating and price_above

    def _bearish_momentum(self) -> bool:
        """Check for bearish MA momentum"""
        threshold = self.hp['slope_threshold']
        accel_threshold = self.hp['acceleration_threshold']

        # Slope is negative and below threshold
        strong_slope = self.current_slope < -threshold

        # Slope is decreasing (negative acceleration)
        decelerating = self.slope_acceleration < -accel_threshold

        # Price below MA
        price_below = self.close < self.ma_sequential[-1]

        return strong_slope and decelerating and price_below

    def should_long(self) -> bool:
        return self._bullish_momentum()

    def should_short(self) -> bool:
        return self._bearish_momentum()

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
        # Exit when momentum reverses
        if self.is_long:
            if self.current_slope < 0 or self.slope_acceleration < -self.hp['acceleration_threshold'] * 2:
                self.liquidate()
        elif self.is_short:
            if self.current_slope > 0 or self.slope_acceleration > self.hp['acceleration_threshold'] * 2:
                self.liquidate()
