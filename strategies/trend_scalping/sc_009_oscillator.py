"""
SC_009: Oscillator Scalp Strategy
---------------------------------
Scalp on quick oscillator reversals.

Entry Long: Multiple oscillators oversold
Entry Short: Multiple oscillators overbought

Optimal Timeframes: 1m, 5m
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class OscillatorScalp(Strategy):
    """Oscillator Scalp Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SC_009"
        self.strategy_name = "Oscillator Scalp"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 5, 'max': 10, 'default': 7},
            {'name': 'stoch_period', 'type': int, 'min': 8, 'max': 14, 'default': 10},
            {'name': 'oversold', 'type': int, 'min': 20, 'max': 30, 'default': 25},
            {'name': 'overbought', 'type': int, 'min': 70, 'max': 80, 'default': 75},
            {'name': 'tp_pct', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'sl_pct', 'type': float, 'min': 0.15, 'max': 0.3, 'default': 0.2},
        ]

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def stoch_k(self) -> float:
        return ta.stoch(self.candles, fastk_period=self.hp['stoch_period'], slowk_period=3, slowd_period=3)[0]

    @property
    def oversold_condition(self) -> bool:
        return self.rsi < self.hp['oversold'] and self.stoch_k < self.hp['oversold']

    @property
    def overbought_condition(self) -> bool:
        return self.rsi > self.hp['overbought'] and self.stoch_k > self.hp['overbought']

    def should_long(self) -> bool:
        # Both oscillators oversold with reversal candle
        return self.oversold_condition and self.close > self.open

    def should_short(self) -> bool:
        # Both oscillators overbought with reversal candle
        return self.overbought_condition and self.close < self.open

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
