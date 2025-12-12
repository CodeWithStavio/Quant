"""
CRYPTO_004: BTC Dominance Proxy Strategy
----------------------------------------
Simulate BTC dominance effects on altcoins.

Entry Long: Falling dominance proxy (altcoin friendly)
Entry Short: Rising dominance proxy (BTC strength)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 10/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BTCDominanceProxy(Strategy):
    """BTC Dominance Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_004"
        self.strategy_name = "BTC Dominance Proxy"
        self.complexity = 6
        self.crypto_suitability = 10

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_ma', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'slow_ma', 'type': int, 'min': 25, 'max': 40, 'default': 30},
            {'name': 'momentum_period', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _dominance_trend(self) -> int:
        """
        Proxy dominance trend using relative strength
        Returns: 1 = rising dominance, -1 = falling dominance, 0 = neutral
        """
        fast = ta.ema(self.candles, period=self.hp['fast_ma'])
        slow = ta.ema(self.candles, period=self.hp['slow_ma'])

        prev_fast = ta.ema(self.candles[:-1], period=self.hp['fast_ma'])
        prev_slow = ta.ema(self.candles[:-1], period=self.hp['slow_ma'])

        # Relative strength change
        current_rs = fast / slow
        prev_rs = prev_fast / prev_slow

        if current_rs < prev_rs * 0.998:  # Falling dominance (good for alts)
            return -1
        elif current_rs > prev_rs * 1.002:  # Rising dominance (bad for alts)
            return 1
        return 0

    @property
    def momentum(self) -> float:
        return ta.roc(self.candles, period=self.hp['momentum_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Falling dominance + positive momentum = alt bullish
        return self._dominance_trend() == -1 and self.momentum > 0

    def should_short(self) -> bool:
        # Rising dominance + negative momentum = alt bearish
        return self._dominance_trend() == 1 and self.momentum < 0

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
        # Exit on trend change
        dominance = self._dominance_trend()
        if self.is_long and dominance == 1:
            self.liquidate()
        elif self.is_short and dominance == -1:
            self.liquidate()
