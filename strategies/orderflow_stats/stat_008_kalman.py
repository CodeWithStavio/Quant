"""
STAT_008: Kalman Filter Strategy
--------------------------------
Trade based on Kalman filter trend estimation.

Entry Long: Price crosses above Kalman line
Entry Short: Price crosses below Kalman line

Optimal Timeframes: 1h, 4h
Complexity: 8/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class KalmanFilter(Strategy):
    """Kalman Filter Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_008"
        self.strategy_name = "Kalman Filter"
        self.complexity = 8
        self.crypto_suitability = 7
        self.kalman_state = None
        self.kalman_cov = 1.0

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'process_noise', 'type': float, 'min': 0.01, 'max': 0.1, 'default': 0.05},
            {'name': 'measurement_noise', 'type': float, 'min': 0.1, 'max': 1.0, 'default': 0.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_kalman(self) -> float:
        """Simple 1D Kalman filter for price"""
        q = self.hp['process_noise']  # Process noise
        r = self.hp['measurement_noise']  # Measurement noise

        # Initialize state with first close if needed
        if self.kalman_state is None:
            self.kalman_state = self.candles[-50, 2] if len(self.candles) > 50 else self.close
            self.kalman_cov = 1.0

        # Prediction step
        pred_state = self.kalman_state
        pred_cov = self.kalman_cov + q

        # Update step
        kalman_gain = pred_cov / (pred_cov + r)
        self.kalman_state = pred_state + kalman_gain * (self.close - pred_state)
        self.kalman_cov = (1 - kalman_gain) * pred_cov

        return self.kalman_state

    def _get_kalman_history(self, lookback: int = 20) -> list:
        """Calculate Kalman filter values for recent history"""
        q = self.hp['process_noise']
        r = self.hp['measurement_noise']

        state = self.candles[-lookback-50, 2] if len(self.candles) > lookback + 50 else self.candles[-lookback, 2]
        cov = 1.0
        history = []

        for i in range(-lookback, 0):
            pred_state = state
            pred_cov = cov + q
            kalman_gain = pred_cov / (pred_cov + r)
            state = pred_state + kalman_gain * (self.candles[i, 2] - pred_state)
            cov = (1 - kalman_gain) * pred_cov
            history.append(state)

        return history

    @property
    def kalman(self) -> float:
        return self._calculate_kalman()

    @property
    def kalman_slope(self) -> float:
        """Calculate Kalman filter slope"""
        history = self._get_kalman_history(10)
        if len(history) < 2:
            return 0
        return history[-1] - history[-5] if len(history) >= 5 else history[-1] - history[0]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        history = self._get_kalman_history(5)
        prev_kalman = history[-2] if len(history) >= 2 else self.kalman
        # Cross above Kalman with positive slope
        cross_above = self.candles[-2, 2] < prev_kalman and self.close > self.kalman
        positive_slope = self.kalman_slope > 0
        return cross_above and positive_slope

    def should_short(self) -> bool:
        history = self._get_kalman_history(5)
        prev_kalman = history[-2] if len(history) >= 2 else self.kalman
        # Cross below Kalman with negative slope
        cross_below = self.candles[-2, 2] > prev_kalman and self.close < self.kalman
        negative_slope = self.kalman_slope < 0
        return cross_below and negative_slope

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
        if self.is_long and self.close < self.kalman:
            self.liquidate()
        elif self.is_short and self.close > self.kalman:
            self.liquidate()
