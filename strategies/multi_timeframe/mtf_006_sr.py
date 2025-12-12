"""
MTF_006: Timeframe Support/Resistance Strategy
----------------------------------------------
Identify S/R levels using multiple period lookbacks.

Entry Long: At HTF support with LTF bounce
Entry Short: At HTF resistance with LTF rejection

Optimal Timeframes: 15m, 1h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TFSupportResistance(Strategy):
    """Timeframe Support/Resistance Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_006"
        self.strategy_name = "TF Support Resistance"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ltf_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'htf_lookback', 'type': int, 'min': 80, 'max': 150, 'default': 100},
            {'name': 'tolerance_pct', 'type': float, 'min': 0.3, 'max': 1.0, 'default': 0.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def htf_support(self) -> float:
        return np.min(self.candles[-self.hp['htf_lookback']:, 4])

    @property
    def htf_resistance(self) -> float:
        return np.max(self.candles[-self.hp['htf_lookback']:, 3])

    @property
    def ltf_support(self) -> float:
        return np.min(self.candles[-self.hp['ltf_lookback']:, 4])

    @property
    def ltf_resistance(self) -> float:
        return np.max(self.candles[-self.hp['ltf_lookback']:, 3])

    @property
    def near_htf_support(self) -> bool:
        tolerance = self.close * (self.hp['tolerance_pct'] / 100)
        return abs(self.low - self.htf_support) <= tolerance

    @property
    def near_htf_resistance(self) -> bool:
        tolerance = self.close * (self.hp['tolerance_pct'] / 100)
        return abs(self.high - self.htf_resistance) <= tolerance

    @property
    def ltf_bounce(self) -> bool:
        return self.close > self.open and self.low <= self.ltf_support * 1.01

    @property
    def ltf_rejection(self) -> bool:
        return self.close < self.open and self.high >= self.ltf_resistance * 0.99

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.near_htf_support and self.ltf_bounce

    def should_short(self) -> bool:
        return self.near_htf_resistance and self.ltf_rejection

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.htf_support - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.htf_resistance + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        pass
