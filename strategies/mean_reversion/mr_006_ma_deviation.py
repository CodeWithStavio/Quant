"""
MR_006: Moving Average Deviation Strategy
-----------------------------------------
Trade extreme deviations from multiple moving averages.

Entry Long: Price far below all MAs
Entry Short: Price far above all MAs

Optimal Timeframes: 15m, 1h
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MADeviationMeanReversion(Strategy):
    """Moving Average Deviation Mean Reversion Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MR_006"
        self.strategy_name = "MA Deviation Mean Reversion"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_ma', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'medium_ma', 'type': int, 'min': 18, 'max': 25, 'default': 20},
            {'name': 'slow_ma', 'type': int, 'min': 45, 'max': 60, 'default': 50},
            {'name': 'deviation_threshold', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    @property
    def fast_ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['fast_ma'])

    @property
    def medium_ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['medium_ma'])

    @property
    def slow_ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['slow_ma'])

    @property
    def avg_ma(self) -> float:
        return (self.fast_ma + self.medium_ma + self.slow_ma) / 3

    @property
    def deviation_from_avg(self) -> float:
        """Percentage deviation from average MA"""
        if self.avg_ma == 0:
            return 0
        return ((self.close - self.avg_ma) / self.avg_ma) * 100

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Price below all MAs with significant deviation
        below_all = self.close < self.fast_ma and self.close < self.medium_ma and self.close < self.slow_ma
        return below_all and self.deviation_from_avg < -self.hp['deviation_threshold']

    def should_short(self) -> bool:
        # Price above all MAs with significant deviation
        above_all = self.close > self.fast_ma and self.close > self.medium_ma and self.close > self.slow_ma
        return above_all and self.deviation_from_avg > self.hp['deviation_threshold']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = self.fast_ma  # Target fastest MA
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = self.fast_ma  # Target fastest MA
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit when price returns to fast MA
        if self.is_long and self.close >= self.fast_ma:
            self.liquidate()
        elif self.is_short and self.close <= self.fast_ma:
            self.liquidate()
