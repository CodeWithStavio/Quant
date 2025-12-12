"""
VOL_008: Money Flow Index (MFI) Strategy
----------------------------------------
Volume-weighted RSI. Uses price and volume together.
MFI > 80 = overbought, MFI < 20 = oversold.

Entry Long: MFI crosses above oversold level
Entry Short: MFI crosses below overbought level

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MFIStrategy(Strategy):
    """Money Flow Index Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_008"
        self.strategy_name = "MFI"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'mfi_period', 'type': int, 'min': 10, 'max': 21, 'default': 14},
            {'name': 'oversold', 'type': float, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'overbought', 'type': float, 'min': 70, 'max': 85, 'default': 80},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _calculate_mfi(self, candles=None) -> float:
        """Calculate Money Flow Index"""
        if candles is None:
            candles = self.candles

        period = self.hp['mfi_period']

        typical_price = (candles[:, 3] + candles[:, 4] + candles[:, 2]) / 3
        raw_money_flow = typical_price * candles[:, 5]

        positive_flow = np.zeros(len(candles))
        negative_flow = np.zeros(len(candles))

        for i in range(1, len(candles)):
            if typical_price[i] > typical_price[i-1]:
                positive_flow[i] = raw_money_flow[i]
            elif typical_price[i] < typical_price[i-1]:
                negative_flow[i] = raw_money_flow[i]

        positive_sum = np.sum(positive_flow[-period:])
        negative_sum = np.sum(negative_flow[-period:])

        if negative_sum == 0:
            return 100

        money_ratio = positive_sum / negative_sum
        mfi = 100 - (100 / (1 + money_ratio))

        return mfi

    @property
    def mfi(self) -> float:
        return self._calculate_mfi()

    @property
    def mfi_prev(self) -> float:
        return self._calculate_mfi(self.candles[:-1])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def mfi_oversold(self) -> bool:
        return self.mfi < self.hp['oversold']

    @property
    def mfi_overbought(self) -> bool:
        return self.mfi > self.hp['overbought']

    @property
    def mfi_crossed_above_oversold(self) -> bool:
        return self.mfi_prev <= self.hp['oversold'] and self.mfi > self.hp['oversold']

    @property
    def mfi_crossed_below_overbought(self) -> bool:
        return self.mfi_prev >= self.hp['overbought'] and self.mfi < self.hp['overbought']

    def should_long(self) -> bool:
        return self.mfi_crossed_above_oversold

    def should_short(self) -> bool:
        return self.mfi_crossed_below_overbought

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
        if self.is_long and self.mfi_overbought:
            self.liquidate()
        elif self.is_short and self.mfi_oversold:
            self.liquidate()
