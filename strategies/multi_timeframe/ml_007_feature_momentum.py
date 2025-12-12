"""
ML_007: Feature Momentum Strategy
---------------------------------
Combine multiple features (indicators) for momentum signal.

Entry Long: Majority of features bullish
Entry Short: Majority of features bearish

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FeatureMomentum(Strategy):
    """Feature Momentum Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_007"
        self.strategy_name = "Feature Momentum"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'rsi_period', 'type': int, 'min': 10, 'max': 18, 'default': 14},
            {'name': 'ma_period', 'type': int, 'min': 18, 'max': 30, 'default': 20},
            {'name': 'mom_period', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'threshold', 'type': int, 'min': 3, 'max': 5, 'default': 4},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _count_bullish_features(self) -> int:
        """Count number of bullish features"""
        count = 0

        # Feature 1: Price above MA
        ma = ta.sma(self.candles, period=self.hp['ma_period'])
        if self.close > ma:
            count += 1

        # Feature 2: RSI trending up
        rsi = ta.rsi(self.candles, period=self.hp['rsi_period'])
        prev_rsi = ta.rsi(self.candles[:-1], period=self.hp['rsi_period'])
        if rsi > prev_rsi:
            count += 1

        # Feature 3: Momentum positive
        mom = ta.roc(self.candles, period=self.hp['mom_period'])
        if mom > 0:
            count += 1

        # Feature 4: Higher close
        if self.close > self.open:
            count += 1

        # Feature 5: ADX trending (strong trend)
        adx = ta.adx(self.candles, period=14)
        if adx > 25:
            di_plus = ta.di(self.candles, period=14)[0]
            di_minus = ta.di(self.candles, period=14)[1]
            if di_plus > di_minus:
                count += 1

        return count

    def _count_bearish_features(self) -> int:
        """Count number of bearish features"""
        count = 0

        # Feature 1: Price below MA
        ma = ta.sma(self.candles, period=self.hp['ma_period'])
        if self.close < ma:
            count += 1

        # Feature 2: RSI trending down
        rsi = ta.rsi(self.candles, period=self.hp['rsi_period'])
        prev_rsi = ta.rsi(self.candles[:-1], period=self.hp['rsi_period'])
        if rsi < prev_rsi:
            count += 1

        # Feature 3: Momentum negative
        mom = ta.roc(self.candles, period=self.hp['mom_period'])
        if mom < 0:
            count += 1

        # Feature 4: Lower close
        if self.close < self.open:
            count += 1

        # Feature 5: ADX trending (strong trend)
        adx = ta.adx(self.candles, period=14)
        if adx > 25:
            di_plus = ta.di(self.candles, period=14)[0]
            di_minus = ta.di(self.candles, period=14)[1]
            if di_minus > di_plus:
                count += 1

        return count

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._count_bullish_features() >= self.hp['threshold']

    def should_short(self) -> bool:
        return self._count_bearish_features() >= self.hp['threshold']

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
        # Exit when features flip
        if self.is_long and self._count_bearish_features() >= 3:
            self.liquidate()
        elif self.is_short and self._count_bullish_features() >= 3:
            self.liquidate()
