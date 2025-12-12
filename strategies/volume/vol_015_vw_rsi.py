"""
VOL_015: Volume-Weighted RSI Strategy
-------------------------------------
RSI weighted by volume for better signal accuracy.
Volume confirms the momentum signals.

Entry Long: VW-RSI crosses above oversold
Entry Short: VW-RSI crosses below overbought

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolumeWeightedRSI(Strategy):
    """Volume-Weighted RSI Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_015"
        self.strategy_name = "Volume Weighted RSI"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 10, 'max': 21, 'default': 14},
            {'name': 'oversold', 'type': float, 'min': 20, 'max': 35, 'default': 30},
            {'name': 'overbought', 'type': float, 'min': 65, 'max': 80, 'default': 70},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_vw_rsi(self, candles=None) -> float:
        """Calculate Volume-Weighted RSI"""
        if candles is None:
            candles = self.candles

        period = self.hp['rsi_period']
        close = candles[:, 2]
        volume = candles[:, 5]

        # Calculate price changes
        changes = np.diff(close)

        # Volume-weighted changes
        vw_changes = changes * volume[1:]

        # Separate gains and losses
        gains = np.where(vw_changes > 0, vw_changes, 0)
        losses = np.where(vw_changes < 0, -vw_changes, 0)

        # Calculate averages
        if len(gains) < period:
            return 50  # Default to neutral

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        vw_rsi = 100 - (100 / (1 + rs))

        return vw_rsi

    @property
    def vw_rsi(self) -> float:
        return self._calculate_vw_rsi()

    @property
    def vw_rsi_prev(self) -> float:
        return self._calculate_vw_rsi(self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def oversold(self) -> bool:
        return self.vw_rsi < self.hp['oversold']

    @property
    def overbought(self) -> bool:
        return self.vw_rsi > self.hp['overbought']

    @property
    def crossed_above_oversold(self) -> bool:
        return self.vw_rsi_prev <= self.hp['oversold'] and self.vw_rsi > self.hp['oversold']

    @property
    def crossed_below_overbought(self) -> bool:
        return self.vw_rsi_prev >= self.hp['overbought'] and self.vw_rsi < self.hp['overbought']

    def should_long(self) -> bool:
        return self.crossed_above_oversold

    def should_short(self) -> bool:
        return self.crossed_below_overbought

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        # Exit at opposite extreme
        if self.is_long and self.overbought:
            self.liquidate()
        elif self.is_short and self.oversold:
            self.liquidate()
