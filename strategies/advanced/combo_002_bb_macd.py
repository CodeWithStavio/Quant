"""
COMBO_002: Bollinger Bands + MACD Combo Strategy
------------------------------------------------
Combine BB bands with MACD momentum.

Entry Long: Price at lower BB + MACD bullish cross
Entry Short: Price at upper BB + MACD bearish cross

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
from typing import List, Dict


class BBMACDCombo(Strategy):
    """BB + MACD Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "COMBO_002"
        self.strategy_name = "BB MACD Combo"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'bb_period', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'bb_std', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def bb(self) -> tuple:
        return ta.bollinger_bands(self.candles, period=self.hp['bb_period'],
                                   devup=self.hp['bb_std'], devdn=self.hp['bb_std'])

    @property
    def macd(self) -> tuple:
        return ta.macd(self.candles, fast_period=12, slow_period=26, signal_period=9)

    @property
    def prev_macd(self) -> tuple:
        return ta.macd(self.candles[:-1], fast_period=12, slow_period=26, signal_period=9)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        upper, mid, lower = self.bb
        at_lower = self.low <= lower

        macd_line, signal, hist = self.macd
        prev_macd_line, prev_signal, _ = self.prev_macd
        macd_cross_up = prev_macd_line <= prev_signal and macd_line > signal

        return at_lower and macd_cross_up

    def should_short(self) -> bool:
        upper, mid, lower = self.bb
        at_upper = self.high >= upper

        macd_line, signal, hist = self.macd
        prev_macd_line, prev_signal, _ = self.prev_macd
        macd_cross_down = prev_macd_line >= prev_signal and macd_line < signal

        return at_upper and macd_cross_down

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = self.bb[1]  # Middle band
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = self.bb[1]  # Middle band
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        macd_line, signal, hist = self.macd
        if self.is_long and macd_line < signal:
            self.liquidate()
        elif self.is_short and macd_line > signal:
            self.liquidate()
