"""
MA_005: Kaufman Adaptive Moving Average (KAMA) Strategy
-------------------------------------------------------
KAMA adapts to market volatility - fast during trends, slow during ranges.

Efficiency Ratio (ER) = Change / Volatility
Smoothing Constant = (ER * (fast_sc - slow_sc) + slow_sc)^2

Entry Long: Price crosses above KAMA when KAMA slope is positive
Entry Short: Price crosses below KAMA when KAMA slope is negative

Optimal Timeframes: 15m, 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class KAMAStrategy(Strategy):
    """Kaufman Adaptive Moving Average Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_005"
        self.strategy_name = "KAMA"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'er_period', 'type': int, 'min': 5, 'max': 20, 'default': 10},
            {'name': 'fast_period', 'type': int, 'min': 2, 'max': 5, 'default': 2},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'slope_lookback', 'type': int, 'min': 3, 'max': 10, 'default': 5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_kama(self, candles=None) -> np.ndarray:
        """Calculate KAMA (sequential)"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]  # Close prices
        er_period = self.hp['er_period']

        # Efficiency Ratio
        change = np.abs(close[er_period:] - close[:-er_period])
        volatility = np.array([np.sum(np.abs(np.diff(close[i:i+er_period+1])))
                              for i in range(len(close) - er_period)])
        volatility[volatility == 0] = 0.0001
        er = change / volatility

        # Smoothing constants
        fast_sc = 2 / (self.hp['fast_period'] + 1)
        slow_sc = 2 / (self.hp['slow_period'] + 1)
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

        # Calculate KAMA
        kama = np.zeros(len(close))
        kama[:er_period] = close[:er_period]
        kama[er_period] = close[er_period]

        for i in range(er_period + 1, len(close)):
            idx = i - er_period - 1
            if idx < len(sc):
                kama[i] = kama[i-1] + sc[idx] * (close[i] - kama[i-1])
            else:
                kama[i] = kama[i-1]

        return kama

    @property
    def kama(self) -> float:
        return self._calculate_kama()[-1]

    @property
    def kama_prev(self) -> float:
        return self._calculate_kama()[-2]

    @property
    def kama_slope(self) -> float:
        kama_seq = self._calculate_kama()
        lookback = self.hp['slope_lookback']
        return kama_seq[-1] - kama_seq[-lookback]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _price_crossed_above_kama(self) -> bool:
        close = self.candles[:, 2]
        kama_seq = self._calculate_kama()
        return close[-2] <= kama_seq[-2] and close[-1] > kama_seq[-1]

    def _price_crossed_below_kama(self) -> bool:
        close = self.candles[:, 2]
        kama_seq = self._calculate_kama()
        return close[-2] >= kama_seq[-2] and close[-1] < kama_seq[-1]

    def should_long(self) -> bool:
        return self._price_crossed_above_kama() and self.kama_slope > 0

    def should_short(self) -> bool:
        return self._price_crossed_below_kama() and self.kama_slope < 0

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
        # Dynamic exit based on KAMA slope reversal
        if self.is_long and self.kama_slope < 0 and self.close < self.kama:
            self.liquidate()
        elif self.is_short and self.kama_slope > 0 and self.close > self.kama:
            self.liquidate()
