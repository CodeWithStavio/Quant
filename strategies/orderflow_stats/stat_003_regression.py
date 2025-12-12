"""
STAT_003: Regression Channel Strategy
-------------------------------------
Trade based on linear regression channels.

Entry Long: Price at lower channel band
Entry Short: Price at upper channel band

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RegressionChannel(Strategy):
    """Regression Channel Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "STAT_003"
        self.strategy_name = "Regression Channel"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 80, 'default': 50},
            {'name': 'channel_width', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_regression(self) -> tuple:
        """Calculate linear regression line and channels"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]
        x = np.arange(lookback)

        # Linear regression
        slope, intercept = np.polyfit(x, prices, 1)

        # Predicted value for current bar
        pred = intercept + slope * (lookback - 1)

        # Standard deviation from regression line
        residuals = prices - (intercept + slope * x)
        std = np.std(residuals)

        upper = pred + std * self.hp['channel_width']
        lower = pred - std * self.hp['channel_width']

        return pred, upper, lower, slope

    @property
    def regression(self) -> tuple:
        return self._calculate_regression()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        pred, upper, lower, slope = self.regression
        # Price at lower band with upward slope
        at_lower = self.close <= lower
        uptrend = slope > 0
        return at_lower and uptrend

    def should_short(self) -> bool:
        pred, upper, lower, slope = self.regression
        # Price at upper band with downward slope
        at_upper = self.close >= upper
        downtrend = slope < 0
        return at_upper and downtrend

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
        pred, upper, lower, slope = self.regression
        # Exit at regression line
        if self.is_long and self.close > pred:
            self.liquidate()
        elif self.is_short and self.close < pred:
            self.liquidate()
