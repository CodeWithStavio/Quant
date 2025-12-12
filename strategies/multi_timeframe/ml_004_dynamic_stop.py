"""
ML_004: Dynamic Stop Loss Strategy
----------------------------------
Dynamically adjust stop loss based on market conditions.

Entry Long: Trend confirmation with adaptive stops
Entry Short: Trend confirmation with adaptive stops

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DynamicStopLoss(Strategy):
    """Dynamic Stop Loss Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_004"
        self.strategy_name = "Dynamic Stop Loss"
        self.complexity = 6
        self.crypto_suitability = 8
        self.entry_atr = None

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 18, 'max': 30, 'default': 20},
            {'name': 'vol_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'base_sl_mult', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'max_sl_mult', 'type': float, 'min': 2.5, 'max': 4.0, 'default': 3.0},
        ]

    @property
    def ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def volatility_ratio(self) -> float:
        """Current volatility vs average"""
        current_atr = self.atr
        avg_atr = np.mean([ta.atr(self.candles[:-(i+1)], period=14)
                          for i in range(self.hp['vol_period'])
                          if len(self.candles) > i + 14])
        if avg_atr == 0:
            return 1.0
        return current_atr / avg_atr

    @property
    def dynamic_sl_mult(self) -> float:
        """Calculate dynamic stop loss multiplier"""
        base = self.hp['base_sl_mult']
        max_mult = self.hp['max_sl_mult']

        # Scale stop loss with volatility
        vol_adj = self.volatility_ratio
        return min(base * vol_adj, max_mult)

    @property
    def bullish(self) -> bool:
        return self.close > self.ma

    @property
    def bearish(self) -> bool:
        return self.close < self.ma

    def should_long(self) -> bool:
        prev_close = self.candles[-2, 2]
        prev_ma = ta.ema(self.candles[:-1], period=self.hp['ma_period'])
        return prev_close <= prev_ma and self.bullish

    def should_short(self) -> bool:
        prev_close = self.candles[-2, 2]
        prev_ma = ta.ema(self.candles[:-1], period=self.hp['ma_period'])
        return prev_close >= prev_ma and self.bearish

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        self.entry_atr = self.atr
        stop = entry - (self.atr * self.dynamic_sl_mult)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        self.entry_atr = self.atr
        stop = entry + (self.atr * self.dynamic_sl_mult)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Trailing stop with dynamic adjustment
        if self.is_long:
            new_stop = self.close - (self.atr * self.dynamic_sl_mult)
            if new_stop > self.stop_loss:
                self.stop_loss = self.position.qty, new_stop
        elif self.is_short:
            new_stop = self.close + (self.atr * self.dynamic_sl_mult)
            if new_stop < self.stop_loss:
                self.stop_loss = self.position.qty, new_stop
