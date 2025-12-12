"""
OF_004: Exhaustion Detector Strategy
------------------------------------
Detect buying/selling exhaustion.

Entry Long: Selling exhaustion (reversal up)
Entry Short: Buying exhaustion (reversal down)

Optimal Timeframes: 15m, 1h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ExhaustionDetector(Strategy):
    """Exhaustion Detector Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "OF_004"
        self.strategy_name = "Exhaustion Detector"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 25, 'default': 15},
            {'name': 'vol_decline', 'type': float, 'min': 0.3, 'max': 0.6, 'default': 0.5},
            {'name': 'trend_bars', 'type': int, 'min': 3, 'max': 7, 'default': 5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _is_selling_exhaustion(self) -> bool:
        """Detect selling exhaustion"""
        lookback = self.hp['lookback']
        trend_bars = self.hp['trend_bars']

        # Count consecutive down bars
        down_bars = 0
        for i in range(1, trend_bars + 1):
            if self.candles[-i, 2] < self.candles[-i, 1]:  # close < open
                down_bars += 1

        in_downtrend = down_bars >= trend_bars - 1

        # Volume declining
        early_vol = np.mean(self.candles[-lookback:-lookback//2, 5])
        recent_vol = np.mean(self.candles[-lookback//2:, 5])
        vol_declining = recent_vol < early_vol * self.hp['vol_decline']

        # RSI oversold
        rsi = ta.rsi(self.candles, period=14)
        oversold = rsi < 35

        return in_downtrend and vol_declining and oversold

    def _is_buying_exhaustion(self) -> bool:
        """Detect buying exhaustion"""
        lookback = self.hp['lookback']
        trend_bars = self.hp['trend_bars']

        # Count consecutive up bars
        up_bars = 0
        for i in range(1, trend_bars + 1):
            if self.candles[-i, 2] > self.candles[-i, 1]:  # close > open
                up_bars += 1

        in_uptrend = up_bars >= trend_bars - 1

        # Volume declining
        early_vol = np.mean(self.candles[-lookback:-lookback//2, 5])
        recent_vol = np.mean(self.candles[-lookback//2:, 5])
        vol_declining = recent_vol < early_vol * self.hp['vol_decline']

        # RSI overbought
        rsi = ta.rsi(self.candles, period=14)
        overbought = rsi > 65

        return in_uptrend and vol_declining and overbought

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_selling_exhaustion()

    def should_short(self) -> bool:
        return self._is_buying_exhaustion()

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
        rsi = ta.rsi(self.candles, period=14)
        if self.is_long and rsi > 55:
            self.liquidate()
        elif self.is_short and rsi < 45:
            self.liquidate()
