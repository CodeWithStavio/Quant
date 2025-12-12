"""
ONCHAIN_004: Holder Behavior Proxy Strategy
-------------------------------------------
Simulate holder behavior through price stability analysis.

Entry Long: Strong holder base (price stability with accumulation)
Entry Short: Weak holder base (price instability with distribution)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class HolderBehaviorProxy(Strategy):
    """Holder Behavior Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ONCHAIN_004"
        self.strategy_name = "Holder Behavior Proxy"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'stability_threshold', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
            {'name': 'trend_strength', 'type': float, 'min': 0.02, 'max': 0.05, 'default': 0.03},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_price_stability(self) -> float:
        """Calculate price stability (lower = more stable)"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns) * 100

    def _calculate_trend_bias(self) -> float:
        """Calculate trend bias (-1 to 1)"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]
        first_half = np.mean(prices[:lookback//2])
        second_half = np.mean(prices[lookback//2:])
        return (second_half - first_half) / first_half

    @property
    def stability(self) -> float:
        return self._calculate_price_stability()

    @property
    def trend_bias(self) -> float:
        return self._calculate_trend_bias()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Strong holders: stable price with upward bias
        stable = self.stability < self.hp['stability_threshold']
        upward = self.trend_bias > self.hp['trend_strength']
        return stable and upward

    def should_short(self) -> bool:
        # Weak holders: unstable price with downward bias
        unstable = self.stability > self.hp['stability_threshold'] * 2
        downward = self.trend_bias < -self.hp['trend_strength']
        return unstable and downward

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
        # Exit on trend reversal
        if self.is_long and self.trend_bias < 0:
            self.liquidate()
        elif self.is_short and self.trend_bias > 0:
            self.liquidate()
