"""
VOL_006: Volume Confirmation Strategy
-------------------------------------
Use volume to confirm trend moves.
Rising volume in direction of trend = confirmation.
Declining volume against trend = potential reversal.

Entry Long: Uptrend with volume confirmation
Entry Short: Downtrend with volume confirmation

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolumeConfirmation(Strategy):
    """Volume Confirmation Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_006"
        self.strategy_name = "Volume Confirmation"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volume_threshold', 'type': float, 'min': 1.1, 'max': 2.0, 'default': 1.3},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    @property
    def ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ma_period'])

    @property
    def ma_prev(self) -> float:
        return ta.ema(self.candles[:-1], period=self.hp['ma_period'])

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['volume_period']:, 5])

    @property
    def current_volume(self) -> float:
        return self.candles[-1, 5]

    @property
    def volume_above_avg(self) -> bool:
        return self.current_volume > self.avg_volume * self.hp['volume_threshold']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def uptrend(self) -> bool:
        return self.close > self.ma and self.ma > self.ma_prev

    @property
    def downtrend(self) -> bool:
        return self.close < self.ma and self.ma < self.ma_prev

    @property
    def bullish_bar(self) -> bool:
        return self.close > self.open

    @property
    def bearish_bar(self) -> bool:
        return self.close < self.open

    def should_long(self) -> bool:
        return self.uptrend and self.bullish_bar and self.volume_above_avg

    def should_short(self) -> bool:
        return self.downtrend and self.bearish_bar and self.volume_above_avg

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
        # Exit on trend reversal
        if self.is_long and self.close < self.ma:
            self.liquidate()
        elif self.is_short and self.close > self.ma:
            self.liquidate()
