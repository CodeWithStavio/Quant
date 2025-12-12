"""
TF_006: Linear Regression Trend Strategy
----------------------------------------
Trade based on linear regression slope direction.

Entry Long: Strong positive slope
Entry Short: Strong negative slope

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class LinearRegressionTrend(Strategy):
    """Linear Regression Trend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_006"
        self.strategy_name = "Linear Regression Trend"
        self.complexity = 5
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'slope_threshold', 'type': float, 'min': 0.001, 'max': 0.005, 'default': 0.002},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.0, 'default': 3.0},
        ]

    def _linear_regression(self) -> tuple:
        """Calculate linear regression line and slope"""
        closes = self.candles[-self.hp['period']:, 2]
        x = np.arange(len(closes))
        y = closes

        # Calculate slope and intercept
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_xx = np.sum(x * x)

        denom = n * sum_xx - sum_x * sum_x
        if denom == 0:
            return 0, 0, 0

        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

        # Current regression value
        current_value = slope * (n - 1) + intercept

        # Normalized slope (as percentage of price)
        norm_slope = slope / current_value if current_value != 0 else 0

        return norm_slope, current_value, slope

    @property
    def slope(self) -> float:
        norm_slope, _, _ = self._linear_regression()
        return norm_slope

    @property
    def regression_value(self) -> float:
        _, value, _ = self._linear_regression()
        return value

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Strong positive slope and price above regression
        return self.slope > self.hp['slope_threshold'] and self.close > self.regression_value

    def should_short(self) -> bool:
        # Strong negative slope and price below regression
        return self.slope < -self.hp['slope_threshold'] and self.close < self.regression_value

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit if slope reverses
        if self.is_long and self.slope < 0:
            self.liquidate()
        elif self.is_short and self.slope > 0:
            self.liquidate()
