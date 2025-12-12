"""
CRYPTO_007: Weekend Effect Strategy
-----------------------------------
Trade based on weekend/weekday patterns.

Entry Long: Weekend dip recovery
Entry Short: Weekend pump fade

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from datetime import datetime
from typing import List, Dict


class WeekendEffect(Strategy):
    """Weekend Effect Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_007"
        self.strategy_name = "Weekend Effect"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'threshold_pct', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _is_weekend(self) -> bool:
        """Check if current time is weekend (Saturday or Sunday)"""
        # Use candle timestamp
        timestamp = self.candles[-1, 0] / 1000  # Convert ms to seconds
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.weekday() >= 5  # 5 = Saturday, 6 = Sunday

    def _is_monday(self) -> bool:
        """Check if current time is Monday"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.weekday() == 0

    def _weekend_change(self) -> float:
        """Calculate price change during weekend"""
        lookback = min(self.hp['lookback'], len(self.candles) - 1)

        # Find last Friday close (approximate)
        friday_price = None
        for i in range(1, lookback):
            ts = self.candles[-i, 0] / 1000
            dt = datetime.utcfromtimestamp(ts)
            if dt.weekday() == 4:  # Friday
                friday_price = self.candles[-i, 2]
                break

        if friday_price is None:
            return 0

        return (self.close - friday_price) / friday_price * 100

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    def should_long(self) -> bool:
        # Monday morning after weekend dip
        if not self._is_monday():
            return False

        weekend_drop = self._weekend_change() < -self.hp['threshold_pct']
        oversold = self.rsi < 40

        return weekend_drop and oversold

    def should_short(self) -> bool:
        # Monday morning after weekend pump
        if not self._is_monday():
            return False

        weekend_pump = self._weekend_change() > self.hp['threshold_pct']
        overbought = self.rsi > 60

        return weekend_pump and overbought

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
        # Exit mid-week
        ts = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(ts)
        if dt.weekday() >= 2:  # Tuesday or later
            self.liquidate()
