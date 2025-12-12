"""
CRYPTO_013: DeFi Momentum Strategy
----------------------------------
Trade based on strong momentum patterns typical of DeFi tokens.

Entry Long: Strong bullish momentum with volume
Entry Short: Strong bearish momentum with volume

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 10/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DeFiMomentum(Strategy):
    """DeFi Momentum Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_013"
        self.strategy_name = "DeFi Momentum"
        self.complexity = 5
        self.crypto_suitability = 10

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'roc_period', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'momentum_threshold', 'type': float, 'min': 3, 'max': 8, 'default': 5},
            {'name': 'volume_surge', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def roc(self) -> float:
        return ta.roc(self.candles, period=self.hp['roc_period'])

    @property
    def prev_roc(self) -> float:
        return ta.roc(self.candles[:-1], period=self.hp['roc_period'])

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def volume_ratio(self) -> float:
        avg_vol = np.mean(self.candles[-20:-1, 5])
        return self.candles[-1, 5] / avg_vol if avg_vol > 0 else 1

    def should_long(self) -> bool:
        # Strong upward momentum with accelerating ROC
        strong_momentum = self.roc > self.hp['momentum_threshold']
        accelerating = self.roc > self.prev_roc
        high_volume = self.volume_ratio > self.hp['volume_surge']
        not_overbought = self.rsi < 75

        return strong_momentum and accelerating and high_volume and not_overbought

    def should_short(self) -> bool:
        # Strong downward momentum with accelerating selling
        strong_momentum = self.roc < -self.hp['momentum_threshold']
        accelerating = self.roc < self.prev_roc
        high_volume = self.volume_ratio > self.hp['volume_surge']
        not_oversold = self.rsi > 25

        return strong_momentum and accelerating and high_volume and not_oversold

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
        # Trail stop on momentum
        if self.is_long:
            if self.roc < 0:
                self.liquidate()
            else:
                trail = self.close - (self.atr * 1.5)
                if trail > self.average_entry_price:
                    self.stop_loss = self.position.qty, trail
        elif self.is_short:
            if self.roc > 0:
                self.liquidate()
            else:
                trail = self.close + (self.atr * 1.5)
                if trail < self.average_entry_price:
                    self.stop_loss = self.position.qty, trail
