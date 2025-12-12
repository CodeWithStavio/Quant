"""
MTF_003: Timeframe Divergence Strategy
--------------------------------------
Trade when lower and higher timeframe views diverge.

Entry Long: HTF bullish, LTF oversold reversal
Entry Short: HTF bearish, LTF overbought reversal

Optimal Timeframes: 15m, 1h
Complexity: 6/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TFDivergence(Strategy):
    """Timeframe Divergence Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_003"
        self.strategy_name = "TF Divergence"
        self.complexity = 6
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'htf_ma', 'type': int, 'min': 150, 'max': 250, 'default': 200},
            {'name': 'ltf_rsi', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'oversold', 'type': int, 'min': 25, 'max': 35, 'default': 30},
            {'name': 'overbought', 'type': int, 'min': 65, 'max': 75, 'default': 70},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def htf_ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['htf_ma'])

    @property
    def htf_bullish(self) -> bool:
        return self.close > self.htf_ma

    @property
    def htf_bearish(self) -> bool:
        return self.close < self.htf_ma

    @property
    def ltf_rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['ltf_rsi'])

    @property
    def prev_rsi(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['ltf_rsi'])

    @property
    def ltf_oversold_bounce(self) -> bool:
        return self.prev_rsi < self.hp['oversold'] and self.ltf_rsi > self.hp['oversold']

    @property
    def ltf_overbought_drop(self) -> bool:
        return self.prev_rsi > self.hp['overbought'] and self.ltf_rsi < self.hp['overbought']

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # HTF bullish trend, LTF oversold bounce
        return self.htf_bullish and self.ltf_oversold_bounce

    def should_short(self) -> bool:
        # HTF bearish trend, LTF overbought drop
        return self.htf_bearish and self.ltf_overbought_drop

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
        # Exit on HTF trend change
        if self.is_long and self.htf_bearish:
            self.liquidate()
        elif self.is_short and self.htf_bullish:
            self.liquidate()
