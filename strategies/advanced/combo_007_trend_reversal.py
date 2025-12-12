"""
COMBO_007: Trend + Reversal Combo Strategy
------------------------------------------
Combine trend following with reversal signals.

Entry Long: Uptrend pullback to support
Entry Short: Downtrend rally to resistance

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
from typing import List, Dict


class TrendReversalCombo(Strategy):
    """Trend + Reversal Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "COMBO_007"
        self.strategy_name = "Trend Reversal Combo"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'trend_ma', 'type': int, 'min': 40, 'max': 80, 'default': 50},
            {'name': 'pullback_ma', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'rsi_oversold', 'type': int, 'min': 30, 'max': 40, 'default': 35},
            {'name': 'rsi_overbought', 'type': int, 'min': 60, 'max': 70, 'default': 65},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def trend_ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['trend_ma'])

    @property
    def pullback_ma(self) -> float:
        return ta.sma(self.candles, period=self.hp['pullback_ma'])

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def is_uptrend(self) -> bool:
        return self.close > self.trend_ma

    @property
    def is_downtrend(self) -> bool:
        return self.close < self.trend_ma

    def should_long(self) -> bool:
        # Uptrend pullback: price above long MA, touching short MA, RSI oversold
        in_uptrend = self.is_uptrend
        pullback = self.low <= self.pullback_ma <= self.high or self.close < self.pullback_ma * 1.01
        oversold = self.rsi < self.hp['rsi_oversold']

        return in_uptrend and pullback and oversold

    def should_short(self) -> bool:
        # Downtrend rally: price below long MA, touching short MA, RSI overbought
        in_downtrend = self.is_downtrend
        rally = self.low <= self.pullback_ma <= self.high or self.close > self.pullback_ma * 0.99
        overbought = self.rsi > self.hp['rsi_overbought']

        return in_downtrend and rally and overbought

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
        if self.is_long and self.close < self.trend_ma:
            self.liquidate()
        elif self.is_short and self.close > self.trend_ma:
            self.liquidate()
