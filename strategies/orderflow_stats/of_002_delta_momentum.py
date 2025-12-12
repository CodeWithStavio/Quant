"""
OF_002: Delta Momentum Strategy
-------------------------------
Trade based on cumulative delta momentum.

Entry Long: Rising cumulative delta
Entry Short: Falling cumulative delta

Optimal Timeframes: 5m, 15m, 1h
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DeltaMomentum(Strategy):
    """Delta Momentum Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "OF_002"
        self.strategy_name = "Delta Momentum"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'delta_threshold', 'type': float, 'min': 0.3, 'max': 0.7, 'default': 0.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _calculate_delta(self, idx: int) -> float:
        """Calculate delta (buy - sell volume) for a candle"""
        candle = self.candles[idx]
        high, low, close, open_price, volume = candle[3], candle[4], candle[2], candle[1], candle[5]

        if high == low:
            return 0

        # Delta based on close position
        buy_ratio = (close - low) / (high - low)
        buy_vol = volume * buy_ratio
        sell_vol = volume * (1 - buy_ratio)

        return buy_vol - sell_vol

    def _cumulative_delta(self) -> np.ndarray:
        """Calculate cumulative delta over lookback"""
        lookback = self.hp['lookback']
        deltas = [self._calculate_delta(-i) for i in range(lookback, 0, -1)]
        return np.cumsum(deltas)

    def _delta_momentum(self) -> float:
        """Calculate delta momentum (slope of cumulative delta)"""
        cum_delta = self._cumulative_delta()
        if len(cum_delta) < 2:
            return 0

        x = np.arange(len(cum_delta))
        slope = np.polyfit(x, cum_delta, 1)[0]
        return slope

    @property
    def delta_mom(self) -> float:
        return self._delta_momentum()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-20:, 5])

    @property
    def normalized_delta_mom(self) -> float:
        """Normalize delta momentum by average volume"""
        return self.delta_mom / self.avg_volume if self.avg_volume > 0 else 0

    def should_long(self) -> bool:
        return self.normalized_delta_mom > self.hp['delta_threshold']

    def should_short(self) -> bool:
        return self.normalized_delta_mom < -self.hp['delta_threshold']

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
        # Exit on delta reversal
        if self.is_long and self.normalized_delta_mom < 0:
            self.liquidate()
        elif self.is_short and self.normalized_delta_mom > 0:
            self.liquidate()
