"""
ML_009: Adaptive RSI Strategy
-----------------------------
RSI with adaptive thresholds based on market conditions.

Entry Long: RSI crosses adaptive oversold level
Entry Short: RSI crosses adaptive overbought level

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class AdaptiveRSI(Strategy):
    """Adaptive RSI Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_009"
        self.strategy_name = "Adaptive RSI"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'lookback', 'type': int, 'min': 60, 'max': 120, 'default': 80},
            {'name': 'base_oversold', 'type': int, 'min': 25, 'max': 35, 'default': 30},
            {'name': 'base_overbought', 'type': int, 'min': 65, 'max': 75, 'default': 70},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def prev_rsi(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['rsi_period'])

    @property
    def rsi_volatility(self) -> float:
        """Calculate RSI volatility over lookback"""
        lookback = self.hp['lookback']
        rsis = []
        for i in range(lookback):
            if len(self.candles) > i + self.hp['rsi_period']:
                r = ta.rsi(self.candles[:-(i+1)], period=self.hp['rsi_period'])
                rsis.append(r)
        return np.std(rsis) if rsis else 10

    @property
    def adaptive_oversold(self) -> float:
        """Adjust oversold level based on RSI volatility"""
        base = self.hp['base_oversold']
        vol = self.rsi_volatility
        # Higher vol = more extreme levels needed
        adjustment = min(vol / 3, 10)
        return base - adjustment

    @property
    def adaptive_overbought(self) -> float:
        """Adjust overbought level based on RSI volatility"""
        base = self.hp['base_overbought']
        vol = self.rsi_volatility
        adjustment = min(vol / 3, 10)
        return base + adjustment

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.prev_rsi < self.adaptive_oversold and self.rsi > self.adaptive_oversold

    def should_short(self) -> bool:
        return self.prev_rsi > self.adaptive_overbought and self.rsi < self.adaptive_overbought

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
        if self.is_long and self.rsi > 50:
            self.liquidate()
        elif self.is_short and self.rsi < 50:
            self.liquidate()
