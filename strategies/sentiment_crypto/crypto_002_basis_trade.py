"""
CRYPTO_002: Basis Trade Proxy Strategy
--------------------------------------
Simulate futures basis using price trends.

Entry Long: Contango narrowing (bullish spot)
Entry Short: Backwardation narrowing (bearish spot)

Optimal Timeframes: 4h, 1d
Complexity: 7/10
Crypto Suitability: 10/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BasisTradeProxy(Strategy):
    """Basis Trade Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_002"
        self.strategy_name = "Basis Trade Proxy"
        self.complexity = 7
        self.crypto_suitability = 10

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 5, 'max': 12, 'default': 8},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 40, 'default': 30},
            {'name': 'basis_threshold', 'type': float, 'min': 0.5, 'max': 2.0, 'default': 1.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_basis_proxy(self) -> float:
        """
        Proxy basis as difference between fast and slow MA
        Positive = contango proxy (futures > spot)
        Negative = backwardation proxy (futures < spot)
        """
        fast_ma = ta.ema(self.candles, period=self.hp['fast_period'])
        slow_ma = ta.ema(self.candles, period=self.hp['slow_period'])

        # Basis as percentage
        return (fast_ma - slow_ma) / slow_ma * 100

    def _prev_basis_proxy(self) -> float:
        """Previous basis proxy"""
        fast_ma = ta.ema(self.candles[:-1], period=self.hp['fast_period'])
        slow_ma = ta.ema(self.candles[:-1], period=self.hp['slow_period'])
        return (fast_ma - slow_ma) / slow_ma * 100

    @property
    def basis(self) -> float:
        return self._calculate_basis_proxy()

    @property
    def prev_basis(self) -> float:
        return self._prev_basis_proxy()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Basis narrowing from negative (backwardation -> flat = bullish)
        threshold = self.hp['basis_threshold']
        return (self.prev_basis < -threshold and
                self.basis > self.prev_basis and
                self.basis > -threshold / 2)

    def should_short(self) -> bool:
        # Basis narrowing from positive (contango -> flat = bearish)
        threshold = self.hp['basis_threshold']
        return (self.prev_basis > threshold and
                self.basis < self.prev_basis and
                self.basis < threshold / 2)

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
        # Exit when basis reverses
        if self.is_long and self.basis < self.prev_basis:
            self.liquidate()
        elif self.is_short and self.basis > self.prev_basis:
            self.liquidate()
