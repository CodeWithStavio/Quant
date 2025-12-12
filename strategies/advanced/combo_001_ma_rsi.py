"""
COMBO_001: MA + RSI Combo Strategy
----------------------------------
Combine moving average trend with RSI confirmation.

Entry Long: Price above MA + RSI crossing above oversold
Entry Short: Price below MA + RSI crossing below overbought

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
from typing import List, Dict


class MARSICombo(Strategy):
    """MA + RSI Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "COMBO_001"
        self.strategy_name = "MA RSI Combo"
        self.complexity = 4
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'rsi_period', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'rsi_oversold', 'type': int, 'min': 25, 'max': 35, 'default': 30},
            {'name': 'rsi_overbought', 'type': int, 'min': 65, 'max': 75, 'default': 70},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['ma_period'])

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def prev_rsi(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['rsi_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        above_ma = self.close > self.ma
        rsi_cross_up = self.prev_rsi < self.hp['rsi_oversold'] and self.rsi > self.hp['rsi_oversold']
        return above_ma and rsi_cross_up

    def should_short(self) -> bool:
        below_ma = self.close < self.ma
        rsi_cross_down = self.prev_rsi > self.hp['rsi_overbought'] and self.rsi < self.hp['rsi_overbought']
        return below_ma and rsi_cross_down

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
        if self.is_long and (self.close < self.ma or self.rsi > 70):
            self.liquidate()
        elif self.is_short and (self.close > self.ma or self.rsi < 30):
            self.liquidate()
