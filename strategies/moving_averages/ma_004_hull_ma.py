"""
MA_004: Hull Moving Average Strategy
------------------------------------
HMA provides the fastest MA with minimal lag.
HMA = WMA(2*WMA(n/2) - WMA(n), sqrt(n))

Entry Long: HMA turns up and price above HMA
Entry Short: HMA turns down and price below HMA

Optimal Timeframes: 5m, 15m, 1h
Complexity: 3/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class HullMACrossover(Strategy):
    """Hull Moving Average Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_004"
        self.strategy_name = "Hull MA"
        self.complexity = 3
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'hma_period', 'type': int, 'min': 9, 'max': 50, 'default': 21},
            {'name': 'confirmation_period', 'type': int, 'min': 2, 'max': 5, 'default': 3},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _calculate_hma(self, candles=None) -> np.ndarray:
        """Calculate Hull Moving Average (sequential)"""
        if candles is None:
            candles = self.candles

        period = self.hp['hma_period']
        half_period = int(period / 2)
        sqrt_period = int(np.sqrt(period))

        # Get WMAs
        wma_half = ta.wma(candles, period=half_period, sequential=True)
        wma_full = ta.wma(candles, period=period, sequential=True)

        # Calculate 2*WMA(n/2) - WMA(n)
        raw_hma = 2 * wma_half - wma_full

        # Create temp candles for final WMA
        temp_candles = candles.copy()
        temp_candles[:, 2] = raw_hma  # Replace close with raw_hma

        # Final HMA
        hma = ta.wma(temp_candles, period=sqrt_period, sequential=True)
        return hma

    @property
    def hma(self) -> float:
        return self._calculate_hma()[-1]

    @property
    def hma_prev(self) -> float:
        return self._calculate_hma()[-2]

    @property
    def hma_slope(self) -> float:
        hma_seq = self._calculate_hma()
        return hma_seq[-1] - hma_seq[-self.hp['confirmation_period']]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _hma_turning_up(self) -> bool:
        """Check if HMA is turning upward"""
        hma_seq = self._calculate_hma()
        recent = hma_seq[-self.hp['confirmation_period']:]
        return all(recent[i] < recent[i+1] for i in range(len(recent)-1))

    def _hma_turning_down(self) -> bool:
        """Check if HMA is turning downward"""
        hma_seq = self._calculate_hma()
        recent = hma_seq[-self.hp['confirmation_period']:]
        return all(recent[i] > recent[i+1] for i in range(len(recent)-1))

    def should_long(self) -> bool:
        return self._hma_turning_up() and self.close > self.hma

    def should_short(self) -> bool:
        return self._hma_turning_down() and self.close < self.hma

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def update_position(self):
        # Trail stop using HMA
        if self.is_long and self.close < self.hma:
            self.liquidate()
        elif self.is_short and self.close > self.hma:
            self.liquidate()
