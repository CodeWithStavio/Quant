"""
ADV_003: Wyckoff Method Strategy
--------------------------------
Trade based on Wyckoff accumulation/distribution phases.

Entry Long: Accumulation spring pattern
Entry Short: Distribution upthrust pattern

Optimal Timeframes: 4h, 1d
Complexity: 8/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class WyckoffMethod(Strategy):
    """Wyckoff Method Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_003"
        self.strategy_name = "Wyckoff Method"
        self.complexity = 8
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'range_lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'range_threshold', 'type': float, 'min': 3, 'max': 8, 'default': 5},
            {'name': 'spring_depth', 'type': float, 'min': 0.5, 'max': 2.0, 'default': 1.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _detect_trading_range(self) -> dict:
        """Detect if in trading range (accumulation/distribution)"""
        lookback = self.hp['range_lookback']
        prices = self.candles[-lookback:, 2]

        range_high = np.max(self.candles[-lookback:, 3])
        range_low = np.min(self.candles[-lookback:, 4])
        range_pct = (range_high - range_low) / np.mean(prices) * 100

        is_range = range_pct < self.hp['range_threshold']

        return {
            'is_range': is_range,
            'high': range_high,
            'low': range_low,
            'mid': (range_high + range_low) / 2
        }

    def _is_spring(self) -> bool:
        """Detect spring pattern (false breakdown)"""
        tr = self._detect_trading_range()
        if not tr['is_range']:
            return False

        # Spring: price briefly breaks below range low then closes back inside
        atr = self.atr
        broke_below = self.low < tr['low'] - (atr * self.hp['spring_depth'] * 0.1)
        closed_inside = self.close > tr['low']
        bullish_close = self.close > self.open

        return broke_below and closed_inside and bullish_close

    def _is_upthrust(self) -> bool:
        """Detect upthrust pattern (false breakout)"""
        tr = self._detect_trading_range()
        if not tr['is_range']:
            return False

        # Upthrust: price briefly breaks above range high then closes back inside
        atr = self.atr
        broke_above = self.high > tr['high'] + (atr * self.hp['spring_depth'] * 0.1)
        closed_inside = self.close < tr['high']
        bearish_close = self.close < self.open

        return broke_above and closed_inside and bearish_close

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_spring()

    def should_short(self) -> bool:
        return self._is_upthrust()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        tr = self._detect_trading_range()
        stop = tr['low'] - (self.atr * 0.5)
        target = tr['high']
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        tr = self._detect_trading_range()
        stop = tr['high'] + (self.atr * 0.5)
        target = tr['low']
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        tr = self._detect_trading_range()
        if self.is_long and self.close > tr['high']:
            # Breakout - trail stop
            trail = self.close - self.atr
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short and self.close < tr['low']:
            trail = self.close + self.atr
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail
