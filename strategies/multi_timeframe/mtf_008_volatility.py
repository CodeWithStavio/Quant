"""
MTF_008: Timeframe Volatility Filter Strategy
---------------------------------------------
Filter trades based on volatility from multiple period views.

Entry Long: Low HTF volatility with LTF breakout
Entry Short: Low HTF volatility with LTF breakdown

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TFVolatilityFilter(Strategy):
    """Timeframe Volatility Filter Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_008"
        self.strategy_name = "TF Volatility Filter"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ltf_atr', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'htf_atr', 'type': int, 'min': 50, 'max': 80, 'default': 60},
            {'name': 'vol_percentile', 'type': float, 'min': 20, 'max': 40, 'default': 30},
            {'name': 'ltf_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def ltf_atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['ltf_atr'])

    @property
    def htf_atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['htf_atr'])

    @property
    def htf_atr_percentile(self) -> float:
        """Calculate where current HTF ATR ranks historically"""
        lookback = 100
        atrs = []
        for i in range(lookback):
            if len(self.candles) > i + self.hp['htf_atr']:
                atr = ta.atr(self.candles[:-(i+1)], period=self.hp['htf_atr'])
                atrs.append(atr)
        if not atrs:
            return 50
        return (np.sum(np.array(atrs) < self.htf_atr) / len(atrs)) * 100

    @property
    def low_htf_volatility(self) -> bool:
        return self.htf_atr_percentile < self.hp['vol_percentile']

    @property
    def ltf_high(self) -> float:
        return np.max(self.candles[-self.hp['ltf_lookback']:-1, 3])

    @property
    def ltf_low(self) -> float:
        return np.min(self.candles[-self.hp['ltf_lookback']:-1, 4])

    def should_long(self) -> bool:
        return self.low_htf_volatility and self.close > self.ltf_high

    def should_short(self) -> bool:
        return self.low_htf_volatility and self.close < self.ltf_low

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.ltf_atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.ltf_atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        pass
