"""
SENT_007: Reversal Sentiment Strategy
-------------------------------------
Detect sentiment shifts using reversal patterns.

Entry Long: Bullish reversal sentiment detected
Entry Short: Bearish reversal sentiment detected

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ReversalSentiment(Strategy):
    """Reversal Sentiment Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SENT_007"
        self.strategy_name = "Reversal Sentiment"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'rsi_oversold', 'type': int, 'min': 20, 'max': 35, 'default': 30},
            {'name': 'rsi_overbought', 'type': int, 'min': 65, 'max': 80, 'default': 70},
            {'name': 'lookback', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=self.hp['rsi_period'])

    @property
    def prev_rsi(self) -> float:
        return ta.rsi(self.candles[:-1], period=self.hp['rsi_period'])

    def _is_bullish_reversal(self) -> bool:
        """Check for bullish reversal pattern"""
        lookback = self.hp['lookback']

        # Check if we were oversold recently
        was_oversold = False
        for i in range(1, lookback + 1):
            if len(self.candles) > i + self.hp['rsi_period']:
                r = ta.rsi(self.candles[:-i], period=self.hp['rsi_period'])
                if r < self.hp['rsi_oversold']:
                    was_oversold = True
                    break

        # RSI crossing up from oversold
        rsi_cross_up = self.prev_rsi < self.hp['rsi_oversold'] and self.rsi > self.hp['rsi_oversold']

        # Bullish candle
        bullish_candle = self.close > self.open

        return (was_oversold or rsi_cross_up) and bullish_candle

    def _is_bearish_reversal(self) -> bool:
        """Check for bearish reversal pattern"""
        lookback = self.hp['lookback']

        # Check if we were overbought recently
        was_overbought = False
        for i in range(1, lookback + 1):
            if len(self.candles) > i + self.hp['rsi_period']:
                r = ta.rsi(self.candles[:-i], period=self.hp['rsi_period'])
                if r > self.hp['rsi_overbought']:
                    was_overbought = True
                    break

        # RSI crossing down from overbought
        rsi_cross_down = self.prev_rsi > self.hp['rsi_overbought'] and self.rsi < self.hp['rsi_overbought']

        # Bearish candle
        bearish_candle = self.close < self.open

        return (was_overbought or rsi_cross_down) and bearish_candle

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_bullish_reversal()

    def should_short(self) -> bool:
        return self._is_bearish_reversal()

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
        # Exit on RSI normalization
        if self.is_long and self.rsi > 60:
            self.liquidate()
        elif self.is_short and self.rsi < 40:
            self.liquidate()
