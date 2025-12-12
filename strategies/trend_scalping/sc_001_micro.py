"""
SC_001: Micro Scalp Strategy
----------------------------
Quick scalps on small price movements.

Entry Long: Quick reversal after micro dip
Entry Short: Quick reversal after micro rally

Optimal Timeframes: 1m, 3m, 5m
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MicroScalp(Strategy):
    """Micro Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_001"
        self.strategy_name = "Micro Scalp"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ema_period', 'type': int, 'min': 5, 'max': 12, 'default': 8},
            {'name': 'rsi_period', 'type': int, 'min': 5, 'max': 10, 'default': 7},
            {'name': 'rsi_oversold', 'type': int, 'min': 25, 'max': 35, 'default': 30},
            {'name': 'rsi_overbought', 'type': int, 'min': 65, 'max': 75, 'default': 70},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    @property
    def ema(self) -> float:
        return ta.ema(self.candles, period=self.hp['ema_period'])

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def prev_rsi(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['rsi_period'])

    def should_long(self) -> bool:
        # RSI bouncing from oversold near EMA
        rsi_bounce = self.prev_rsi < self.hp['rsi_oversold'] and self.rsi > self.hp['rsi_oversold']
        near_ema = abs(self.close - self.ema) / self.close < 0.01
        return rsi_bounce and (near_ema or self.close > self.ema)

    def should_short(self) -> bool:
        # RSI dropping from overbought near EMA
        rsi_drop = self.prev_rsi > self.hp['rsi_overbought'] and self.rsi < self.hp['rsi_overbought']
        near_ema = abs(self.close - self.ema) / self.close < 0.01
        return rsi_drop and (near_ema or self.close < self.ema)

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry * (1 - self.hp['sl_pct'] / 100)
        target = entry * (1 + self.hp['tp_pct'] / 100)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry * (1 + self.hp['sl_pct'] / 100)
        target = entry * (1 - self.hp['tp_pct'] / 100)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        pass
