"""
ADV_001: Fractal Strategy
-------------------------
Trade based on Bill Williams fractal patterns.

Entry Long: Bullish fractal with trend confirmation
Entry Short: Bearish fractal with trend confirmation

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FractalStrategy(Strategy):
    """Fractal Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_001"
        self.strategy_name = "Fractal Strategy"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fractal_bars', 'type': int, 'min': 2, 'max': 5, 'default': 2},
            {'name': 'trend_period', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _is_bullish_fractal(self, idx: int) -> bool:
        """Check for bullish fractal (swing low)"""
        n = self.hp['fractal_bars']
        if abs(idx) + n >= len(self.candles):
            return False

        center_low = self.candles[idx, 4]

        # Check n bars before and after
        for i in range(1, n + 1):
            if self.candles[idx - i, 4] <= center_low:
                return False
            if self.candles[idx + i, 4] <= center_low:
                return False

        return True

    def _is_bearish_fractal(self, idx: int) -> bool:
        """Check for bearish fractal (swing high)"""
        n = self.hp['fractal_bars']
        if abs(idx) + n >= len(self.candles):
            return False

        center_high = self.candles[idx, 3]

        for i in range(1, n + 1):
            if self.candles[idx - i, 3] >= center_high:
                return False
            if self.candles[idx + i, 3] >= center_high:
                return False

        return True

    def _find_recent_bullish_fractal(self) -> float:
        """Find most recent bullish fractal level"""
        n = self.hp['fractal_bars']
        for i in range(n + 1, 20):
            if self._is_bullish_fractal(-i):
                return self.candles[-i, 4]
        return None

    def _find_recent_bearish_fractal(self) -> float:
        """Find most recent bearish fractal level"""
        n = self.hp['fractal_bars']
        for i in range(n + 1, 20):
            if self._is_bearish_fractal(-i):
                return self.candles[-i, 3]
        return None

    @property
    def trend(self) -> int:
        ma = ta.sma(self.candles, period=self.hp['trend_period'])
        if self.close > ma:
            return 1
        elif self.close < ma:
            return -1
        return 0

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        bullish_fractal = self._find_recent_bullish_fractal()
        if bullish_fractal is None:
            return False

        # Price bouncing off fractal support in uptrend
        near_fractal = self.low <= bullish_fractal * 1.005
        uptrend = self.trend == 1
        bullish_candle = self.close > self.open

        return near_fractal and uptrend and bullish_candle

    def should_short(self) -> bool:
        bearish_fractal = self._find_recent_bearish_fractal()
        if bearish_fractal is None:
            return False

        # Price rejected at fractal resistance in downtrend
        near_fractal = self.high >= bearish_fractal * 0.995
        downtrend = self.trend == -1
        bearish_candle = self.close < self.open

        return near_fractal and downtrend and bearish_candle

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        fractal = self._find_recent_bullish_fractal()
        stop = fractal - (self.atr * 0.5) if fractal else entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        fractal = self._find_recent_bearish_fractal()
        stop = fractal + (self.atr * 0.5) if fractal else entry + (self.atr * 2)
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()
