"""
SEASON_003: Intraday Seasonality Strategy
-----------------------------------------
Trade based on time-of-day patterns.

Entry Long: Bullish session times with momentum
Entry Short: Bearish session times with momentum

Optimal Timeframes: 15m, 1h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from datetime import datetime
from typing import List, Dict


class IntradaySeason(Strategy):
    """Intraday Seasonality Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SEASON_003"
        self.strategy_name = "Intraday Season"
        self.complexity = 5
        self.crypto_suitability = 8
        # Active trading hours in UTC
        self.active_hours = list(range(8, 16)) + list(range(14, 22))  # London + NY overlap

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'active_start', 'type': int, 'min': 7, 'max': 10, 'default': 8},
            {'name': 'active_end', 'type': int, 'min': 20, 'max': 23, 'default': 21},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
        ]

    def _get_hour(self) -> int:
        """Get current hour in UTC"""
        timestamp = self.candles[-1, 0] / 1000
        dt = datetime.utcfromtimestamp(timestamp)
        return dt.hour

    @property
    def is_active_session(self) -> bool:
        hour = self._get_hour()
        return self.hp['active_start'] <= hour < self.hp['active_end']

    @property
    def momentum(self) -> float:
        return ta.roc(self.candles, period=5)

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    def should_long(self) -> bool:
        return self.is_active_session and self.momentum > 0.5 and self.rsi < 65

    def should_short(self) -> bool:
        return self.is_active_session and self.momentum < -0.5 and self.rsi > 35

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
        # Exit at end of active session
        if not self.is_active_session:
            self.liquidate()
