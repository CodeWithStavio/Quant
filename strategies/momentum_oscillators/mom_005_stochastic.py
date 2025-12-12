"""
MOM_005: Stochastic Oscillator Strategy
---------------------------------------
Classic Stochastic %K and %D crossover in extreme zones.

Entry Long: %K crosses above %D in oversold zone (<20)
Entry Short: %K crosses below %D in overbought zone (>80)

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class StochasticOscillator(Strategy):
    """Stochastic Oscillator Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_005"
        self.strategy_name = "Stochastic Oscillator"
        self.complexity = 3
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'k_period', 'type': int, 'min': 5, 'max': 21, 'default': 14},
            {'name': 'd_period', 'type': int, 'min': 3, 'max': 5, 'default': 3},
            {'name': 'slowing', 'type': int, 'min': 1, 'max': 5, 'default': 3},
            {'name': 'overbought', 'type': int, 'min': 75, 'max': 90, 'default': 80},
            {'name': 'oversold', 'type': int, 'min': 10, 'max': 25, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 2.5},
        ]

    def _get_stochastic(self, candles=None):
        """Get Stochastic K and D values"""
        if candles is None:
            candles = self.candles
        return ta.stoch(
            candles,
            fastk_period=self.hp['k_period'],
            slowk_period=self.hp['slowing'],
            slowd_period=self.hp['d_period']
        )

    @property
    def stoch_k(self) -> float:
        k, d = self._get_stochastic()
        return k

    @property
    def stoch_d(self) -> float:
        k, d = self._get_stochastic()
        return d

    @property
    def stoch_k_prev(self) -> float:
        k, d = self._get_stochastic(self.candles[:-1])
        return k

    @property
    def stoch_d_prev(self) -> float:
        k, d = self._get_stochastic(self.candles[:-1])
        return d

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _bullish_cross_in_oversold(self) -> bool:
        """K crosses above D in oversold zone"""
        crossed = self.stoch_k_prev <= self.stoch_d_prev and self.stoch_k > self.stoch_d
        in_zone = self.stoch_k < self.hp['oversold'] + 10  # Give some buffer
        return crossed and in_zone

    def _bearish_cross_in_overbought(self) -> bool:
        """K crosses below D in overbought zone"""
        crossed = self.stoch_k_prev >= self.stoch_d_prev and self.stoch_k < self.stoch_d
        in_zone = self.stoch_k > self.hp['overbought'] - 10  # Give some buffer
        return crossed and in_zone

    def should_long(self) -> bool:
        return self._bullish_cross_in_oversold()

    def should_short(self) -> bool:
        return self._bearish_cross_in_overbought()

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
        # Exit on opposite zone
        if self.is_long and self.stoch_k > self.hp['overbought']:
            self.liquidate()
        elif self.is_short and self.stoch_k < self.hp['oversold']:
            self.liquidate()
