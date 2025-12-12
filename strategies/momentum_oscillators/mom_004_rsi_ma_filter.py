"""
MOM_004: RSI with MA Filter Strategy
------------------------------------
RSI signals filtered by trend direction from moving average.

Entry Long: RSI oversold AND price > 200 EMA (oversold in uptrend)
Entry Short: RSI overbought AND price < 200 EMA (overbought in downtrend)

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RSIWithMAFilter(Strategy):
    """RSI with MA Filter Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_004"
        self.strategy_name = "RSI + MA Filter"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'ma_period', 'type': int, 'min': 100, 'max': 200, 'default': 200},
            {'name': 'overbought', 'type': int, 'min': 65, 'max': 80, 'default': 70},
            {'name': 'oversold', 'type': int, 'min': 20, 'max': 35, 'default': 30},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def rsi_prev(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['rsi_period'])

    @property
    def trend_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _uptrend(self) -> bool:
        return self.close > self.trend_ma

    def _downtrend(self) -> bool:
        return self.close < self.trend_ma

    def _rsi_crossed_above_oversold(self) -> bool:
        return self.rsi_prev <= self.hp['oversold'] and self.rsi > self.hp['oversold']

    def _rsi_crossed_below_overbought(self) -> bool:
        return self.rsi_prev >= self.hp['overbought'] and self.rsi < self.hp['overbought']

    def should_long(self) -> bool:
        return self._rsi_crossed_above_oversold() and self._uptrend()

    def should_short(self) -> bool:
        return self._rsi_crossed_below_overbought() and self._downtrend()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = max(self.trend_ma * 0.98, entry - (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = min(self.trend_ma * 1.02, entry + (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        # Exit if trend filter breaks
        if self.is_long and self._downtrend():
            self.liquidate()
        elif self.is_short and self._uptrend():
            self.liquidate()
