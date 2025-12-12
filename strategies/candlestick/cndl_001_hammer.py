"""
CNDL_001: Hammer/Hanging Man Strategy
-------------------------------------
Hammer at bottom = bullish reversal.
Hanging Man at top = bearish warning.

Entry Long: Hammer at support
Entry Short: Hanging Man at resistance

Optimal Timeframes: 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class HammerStrategy(Strategy):
    """Hammer/Hanging Man Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CNDL_001"
        self.strategy_name = "Hammer"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'body_ratio', 'type': float, 'min': 0.2, 'max': 0.4, 'default': 0.3},
            {'name': 'shadow_ratio', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
            {'name': 'trend_period', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 3.0},
        ]

    def _is_hammer(self, idx=-1) -> bool:
        """Check if candle is a hammer (bullish reversal)"""
        o = self.candles[idx, 1]
        c = self.candles[idx, 2]
        h = self.candles[idx, 3]
        l = self.candles[idx, 4]

        body = abs(c - o)
        total_range = h - l
        if total_range == 0:
            return False

        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l

        # Hammer: small body, long lower shadow, small upper shadow
        body_pct = body / total_range
        shadow_ratio = lower_shadow / body if body > 0 else 0

        return (body_pct < self.hp['body_ratio'] and
                shadow_ratio >= self.hp['shadow_ratio'] and
                upper_shadow < body)

    def _is_hanging_man(self, idx=-1) -> bool:
        """Check if candle is a hanging man (bearish warning)"""
        # Same shape as hammer but at top of trend
        return self._is_hammer(idx)

    def _in_downtrend(self) -> bool:
        """Check if in downtrend"""
        period = self.hp['trend_period']
        ma = np.mean(self.candles[-period:, 2])
        return self.close < ma and ma < np.mean(self.candles[-period*2:-period, 2])

    def _in_uptrend(self) -> bool:
        """Check if in uptrend"""
        period = self.hp['trend_period']
        ma = np.mean(self.candles[-period:, 2])
        return self.close > ma and ma > np.mean(self.candles[-period*2:-period, 2])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_hammer() and self._in_downtrend()

    def should_short(self) -> bool:
        return self._is_hanging_man() and self._in_uptrend()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        pass
