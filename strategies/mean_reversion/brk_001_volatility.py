"""
BRK_001: Volatility Breakout Strategy
-------------------------------------
Trade breakouts during volatility expansion.

Entry Long: Price breaks above resistance during volatility expansion
Entry Short: Price breaks below support during volatility expansion

Optimal Timeframes: 15m, 1h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolatilityBreakout(Strategy):
    """Volatility Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BRK_001"
        self.strategy_name = "Volatility Breakout"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'vol_expansion', 'type': float, 'min': 1.2, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def current_atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def avg_atr(self) -> float:
        """Average ATR over lookback period"""
        atrs = []
        for i in range(self.hp['lookback']):
            if len(self.candles) > i + 14:
                atr = ta.atr(self.candles[:-(i+1)], period=14)
                atrs.append(atr)
        return np.mean(atrs) if atrs else self.current_atr

    @property
    def volatility_expanding(self) -> bool:
        """Check if volatility is expanding"""
        return self.current_atr > self.avg_atr * self.hp['vol_expansion']

    @property
    def resistance(self) -> float:
        return np.max(self.candles[-self.hp['lookback']:, 3])

    @property
    def support(self) -> float:
        return np.min(self.candles[-self.hp['lookback']:, 4])

    @property
    def prev_resistance(self) -> float:
        return np.max(self.candles[-(self.hp['lookback']+1):-1, 3])

    @property
    def prev_support(self) -> float:
        return np.min(self.candles[-(self.hp['lookback']+1):-1, 4])

    def should_long(self) -> bool:
        # Breakout above resistance with volatility expansion
        prev_close = self.candles[-2, 2]
        return (self.volatility_expanding and
                prev_close <= self.prev_resistance and
                self.close > self.resistance)

    def should_short(self) -> bool:
        # Breakdown below support with volatility expansion
        prev_close = self.candles[-2, 2]
        return (self.volatility_expanding and
                prev_close >= self.prev_support and
                self.close < self.support)

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.current_atr * self.hp['atr_multiplier_sl'])
        target = entry + (self.current_atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.current_atr * self.hp['atr_multiplier_sl'])
        target = entry - (self.current_atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
