"""
MA_008: Arnaud Legoux Moving Average (ALMA) Strategy
----------------------------------------------------
ALMA uses Gaussian distribution curve for weighting.
Provides smooth response with reduced lag.

Parameters:
- window: lookback period
- offset: controls responsiveness (0.85 typical)
- sigma: controls smoothness (6 typical)

Entry Long: Price crosses above ALMA
Entry Short: Price crosses below ALMA

Optimal Timeframes: 15m, 1h, 4h
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ALMAStrategy(Strategy):
    """Arnaud Legoux Moving Average Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_008"
        self.strategy_name = "ALMA"
        self.complexity = 5
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'window', 'type': int, 'min': 5, 'max': 30, 'default': 9},
            {'name': 'offset', 'type': float, 'min': 0.5, 'max': 1.0, 'default': 0.85},
            {'name': 'sigma', 'type': float, 'min': 2.0, 'max': 10.0, 'default': 6.0},
            {'name': 'trend_period', 'type': int, 'min': 50, 'max': 200, 'default': 100},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _calculate_alma(self, candles=None) -> np.ndarray:
        """Calculate ALMA (sequential)"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]
        window = self.hp['window']
        offset = self.hp['offset']
        sigma = self.hp['sigma']

        m = int(offset * (window - 1))
        s = window / sigma

        # Calculate weights
        weights = np.exp(-((np.arange(window) - m) ** 2) / (2 * s * s))
        weights = weights / np.sum(weights)

        # Calculate ALMA
        alma = np.zeros(len(close))
        for i in range(window - 1, len(close)):
            alma[i] = np.sum(close[i-window+1:i+1] * weights)

        return alma

    @property
    def alma(self) -> float:
        return self._calculate_alma()[-1]

    @property
    def alma_prev(self) -> float:
        return self._calculate_alma()[-2]

    @property
    def trend_ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['trend_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _price_crossed_above(self) -> bool:
        alma = self._calculate_alma()
        return self.candles[-2, 2] <= alma[-2] and self.candles[-1, 2] > alma[-1]

    def _price_crossed_below(self) -> bool:
        alma = self._calculate_alma()
        return self.candles[-2, 2] >= alma[-2] and self.candles[-1, 2] < alma[-1]

    def should_long(self) -> bool:
        return self._price_crossed_above() and self.close > self.trend_ma

    def should_short(self) -> bool:
        return self._price_crossed_below() and self.close < self.trend_ma

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
        if self.is_long and self._price_crossed_below():
            self.liquidate()
        elif self.is_short and self._price_crossed_above():
            self.liquidate()
