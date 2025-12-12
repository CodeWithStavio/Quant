"""
MTF_009: Timeframe Oscillator Confluence Strategy
-------------------------------------------------
Trade when oscillators align across timeframe views.

Entry Long: Both LTF and HTF oscillators oversold and turning up
Entry Short: Both LTF and HTF oscillators overbought and turning down

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TFOscillatorConfluence(Strategy):
    """Timeframe Oscillator Confluence Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_009"
        self.strategy_name = "TF Oscillator Confluence"
        self.complexity = 5
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ltf_rsi', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'htf_rsi', 'type': int, 'min': 50, 'max': 80, 'default': 60},
            {'name': 'oversold', 'type': int, 'min': 25, 'max': 35, 'default': 30},
            {'name': 'overbought', 'type': int, 'min': 65, 'max': 75, 'default': 70},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def ltf_rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['ltf_rsi'])

    @property
    def prev_ltf_rsi(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['ltf_rsi'])

    @property
    def htf_rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['htf_rsi'])

    @property
    def prev_htf_rsi(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['htf_rsi'])

    @property
    def ltf_oversold_turn(self) -> bool:
        return self.ltf_rsi < self.hp['oversold'] + 10 and self.ltf_rsi > self.prev_ltf_rsi

    @property
    def htf_oversold_turn(self) -> bool:
        return self.htf_rsi < self.hp['oversold'] + 15 and self.htf_rsi > self.prev_htf_rsi

    @property
    def ltf_overbought_turn(self) -> bool:
        return self.ltf_rsi > self.hp['overbought'] - 10 and self.ltf_rsi < self.prev_ltf_rsi

    @property
    def htf_overbought_turn(self) -> bool:
        return self.htf_rsi > self.hp['overbought'] - 15 and self.htf_rsi < self.prev_htf_rsi

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.ltf_oversold_turn and self.htf_oversold_turn

    def should_short(self) -> bool:
        return self.ltf_overbought_turn and self.htf_overbought_turn

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
        if self.is_long and self.ltf_rsi > 50:
            self.liquidate()
        elif self.is_short and self.ltf_rsi < 50:
            self.liquidate()
