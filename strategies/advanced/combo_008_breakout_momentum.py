"""
COMBO_008: Breakout + Momentum Combo Strategy
---------------------------------------------
Combine breakout signals with momentum confirmation.

Entry Long: Breakout above resistance + Strong momentum
Entry Short: Breakout below support + Strong momentum

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BreakoutMomentumCombo(Strategy):
    """Breakout + Momentum Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "COMBO_008"
        self.strategy_name = "Breakout Momentum Combo"
        self.complexity = 5
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'mom_threshold', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'vol_multiplier', 'type': float, 'min': 1.3, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    @property
    def resistance(self) -> float:
        return np.max(self.candles[-self.hp['lookback']:-1, 3])

    @property
    def support(self) -> float:
        return np.min(self.candles[-self.hp['lookback']:-1, 4])

    @property
    def momentum(self) -> float:
        return ta.roc(self.candles, period=5)

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['lookback']:-1, 5])

    @property
    def volume_surge(self) -> bool:
        return self.candles[-1, 5] > self.avg_volume * self.hp['vol_multiplier']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        breakout = self.close > self.resistance
        strong_mom = self.momentum > self.hp['mom_threshold']

        return breakout and strong_mom and self.volume_surge

    def should_short(self) -> bool:
        breakdown = self.close < self.support
        strong_mom = self.momentum < -self.hp['mom_threshold']

        return breakdown and strong_mom and self.volume_surge

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.resistance - (self.atr * 0.5)  # Just below breakout level
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.support + (self.atr * 0.5)  # Just above breakdown level
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Trail with ATR
        if self.is_long:
            trail = self.close - (self.atr * 1.5)
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short:
            trail = self.close + (self.atr * 1.5)
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail
