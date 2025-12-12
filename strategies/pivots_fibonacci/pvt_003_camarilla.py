"""
PVT_003: Camarilla Pivot Points Strategy
----------------------------------------
Nick Stott's Camarilla equation pivots.
Tighter levels for intraday trading.

Entry Long: Bounce off S3/S4 levels
Entry Short: Bounce off R3/R4 levels

Optimal Timeframes: 5m, 15m, 1h
Complexity: 4/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class CamarillaPivots(Strategy):
    """Camarilla Pivot Points Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "PVT_003"
        self.strategy_name = "Camarilla Pivots"
        self.complexity = 4
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 24, 'max': 96, 'default': 48},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _calculate_camarilla(self):
        """Calculate Camarilla pivot points"""
        lookback = self.hp['lookback']
        candles = self.candles[-lookback:-1]

        h = np.max(candles[:, 3])
        l = np.min(candles[:, 4])
        c = candles[-1, 2]

        range_hl = h - l

        r4 = c + range_hl * 1.1 / 2
        r3 = c + range_hl * 1.1 / 4
        r2 = c + range_hl * 1.1 / 6
        r1 = c + range_hl * 1.1 / 12
        s1 = c - range_hl * 1.1 / 12
        s2 = c - range_hl * 1.1 / 6
        s3 = c - range_hl * 1.1 / 4
        s4 = c - range_hl * 1.1 / 2

        return {'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4, 's1': s1, 's2': s2, 's3': s3, 's4': s4}

    @property
    def pivots(self) -> dict:
        return self._calculate_camarilla()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        pivots = self.pivots
        # Long at S3/S4 with reversal confirmation
        if self.low <= pivots['s3'] and self.close > pivots['s3'] and self.close > self.open:
            return True
        if self.low <= pivots['s4'] and self.close > pivots['s4'] and self.close > self.open:
            return True
        return False

    def should_short(self) -> bool:
        pivots = self.pivots
        # Short at R3/R4 with reversal confirmation
        if self.high >= pivots['r3'] and self.close < pivots['r3'] and self.close < self.open:
            return True
        if self.high >= pivots['r4'] and self.close < pivots['r4'] and self.close < self.open:
            return True
        return False

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        pivots = self.pivots
        stop = pivots['s4'] - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, pivots['r1']

    def go_short(self):
        entry = self.price
        pivots = self.pivots
        stop = pivots['r4'] + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, pivots['s1']

    def update_position(self):
        pass
