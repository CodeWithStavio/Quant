"""
MTF_007: Timeframe Volume Confirmation Strategy
-----------------------------------------------
Confirm signals with volume from multiple period views.

Entry Long: Price breakout with volume confirmation on both views
Entry Short: Price breakdown with volume confirmation on both views

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TFVolumeConfirmation(Strategy):
    """Timeframe Volume Confirmation Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_007"
        self.strategy_name = "TF Volume Confirmation"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ltf_vol_period', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'htf_vol_period', 'type': int, 'min': 80, 'max': 120, 'default': 100},
            {'name': 'vol_mult', 'type': float, 'min': 1.3, 'max': 2.0, 'default': 1.5},
            {'name': 'price_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def ltf_avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['ltf_vol_period']:-1, 5])

    @property
    def htf_avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['htf_vol_period']:-1, 5])

    @property
    def ltf_volume_spike(self) -> bool:
        return self.current_volume > self.ltf_avg_volume * self.hp['vol_mult']

    @property
    def htf_volume_spike(self) -> bool:
        return self.current_volume > self.htf_avg_volume * self.hp['vol_mult']

    @property
    def price_high(self) -> float:
        return np.max(self.candles[-self.hp['price_lookback']:-1, 3])

    @property
    def price_low(self) -> float:
        return np.min(self.candles[-self.hp['price_lookback']:-1, 4])

    @property
    def breakout_up(self) -> bool:
        return self.close > self.price_high

    @property
    def breakout_down(self) -> bool:
        return self.close < self.price_low

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.breakout_up and self.ltf_volume_spike and self.htf_volume_spike

    def should_short(self) -> bool:
        return self.breakout_down and self.ltf_volume_spike and self.htf_volume_spike

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        pass
