"""
BB_002: Bollinger Band Breakout Strategy
----------------------------------------
Trade breakouts beyond Bollinger Bands with volume confirmation.

Entry Long: Price closes above upper band with volume
Entry Short: Price closes below lower band with volume

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BBBreakout(Strategy):
    """Bollinger Band Breakout Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BB_002"
        self.strategy_name = "BB Breakout"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'std_dev', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'volume_multiplier', 'type': float, 'min': 1.2, 'max': 2.5, 'default': 1.5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _get_bb(self):
        return ta.bollinger_bands(
            self.candles,
            period=self.hp['period'],
            devup=self.hp['std_dev'],
            devdn=self.hp['std_dev']
        )

    @property
    def bb_upper(self) -> float:
        upper, middle, lower = self._get_bb()
        return upper

    @property
    def bb_lower(self) -> float:
        upper, middle, lower = self._get_bb()
        return lower

    @property
    def volume_sma(self) -> float:
        return ta.sma(self.candles, period=20, source_type='volume')

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def high_volume(self) -> bool:
        return self.current_volume > self.volume_sma * self.hp['volume_multiplier']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.close > self.bb_upper and self.high_volume

    def should_short(self) -> bool:
        return self.close < self.bb_lower and self.high_volume

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.bb_upper - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = self.bb_lower + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        # Trail stop to middle band
        upper, middle, lower = self._get_bb()
        if self.is_long and self.close < middle:
            self.liquidate()
        elif self.is_short and self.close > middle:
            self.liquidate()
