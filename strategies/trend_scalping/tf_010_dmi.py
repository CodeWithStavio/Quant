"""
TF_010: Directional Movement Index Trend Strategy
-------------------------------------------------
Trade based on DMI crossovers with ADX filter.

Entry Long: +DI crosses above -DI with rising ADX
Entry Short: -DI crosses above +DI with rising ADX

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DMITrend(Strategy):
    """DMI Trend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_010"
        self.strategy_name = "DMI Trend"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'dmi_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'adx_threshold', 'type': int, 'min': 18, 'max': 28, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def di_plus(self) -> float:
        return ta.di(self.candles, period=self.hp['dmi_period'])[0]

    @property
    def di_minus(self) -> float:
        return ta.di(self.candles, period=self.hp['dmi_period'])[1]

    @property
    def prev_di_plus(self) -> float:
        return ta.di(self.candles[:-1], period=self.hp['dmi_period'])[0]

    @property
    def prev_di_minus(self) -> float:
        return ta.di(self.candles[:-1], period=self.hp['dmi_period'])[1]

    @property
    def adx(self) -> float:
        return ta.adx(self.candles, period=self.hp['dmi_period'])

    @property
    def prev_adx(self) -> float:
        return ta.adx(self.candles[:-1], period=self.hp['dmi_period'])

    @property
    def adx_rising(self) -> bool:
        return self.adx > self.prev_adx

    @property
    def adx_strong(self) -> bool:
        return self.adx > self.hp['adx_threshold']

    @property
    def bullish_cross(self) -> bool:
        return self.prev_di_plus <= self.prev_di_minus and self.di_plus > self.di_minus

    @property
    def bearish_cross(self) -> bool:
        return self.prev_di_plus >= self.prev_di_minus and self.di_plus < self.di_minus

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.bullish_cross and (self.adx_strong or self.adx_rising)

    def should_short(self) -> bool:
        return self.bearish_cross and (self.adx_strong or self.adx_rising)

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = entry + (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = entry - (self.atr * self.hp['atr_multiplier_tp'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit on DI cross reversal
        if self.is_long and self.di_plus < self.di_minus:
            self.liquidate()
        elif self.is_short and self.di_plus > self.di_minus:
            self.liquidate()
