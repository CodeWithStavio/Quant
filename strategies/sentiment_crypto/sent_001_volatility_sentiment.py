"""
SENT_001: Volatility Sentiment Strategy
---------------------------------------
Use volatility as a proxy for market sentiment.

Entry Long: Low volatility expansion after contraction (fear -> greed)
Entry Short: High volatility spike (panic selling)

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolatilitySentiment(Strategy):
    """Volatility-based Sentiment Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SENT_001"
        self.strategy_name = "Volatility Sentiment"
        self.complexity = 5
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'atr_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'lookback', 'type': int, 'min': 40, 'max': 80, 'default': 50},
            {'name': 'low_vol_percentile', 'type': float, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'high_vol_percentile', 'type': float, 'min': 80, 'max': 95, 'default': 90},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    @property
    def atr_history(self) -> np.ndarray:
        """Get ATR history for percentile calculation"""
        atrs = []
        for i in range(self.hp['lookback']):
            if len(self.candles) > i + self.hp['atr_period']:
                atr = ta.atr(self.candles[:-(i+1)], period=self.hp['atr_period'])
                atrs.append(atr)
        return np.array(atrs) if atrs else np.array([self.atr])

    @property
    def vol_percentile(self) -> float:
        """Current volatility percentile"""
        history = self.atr_history
        return np.sum(history < self.atr) / len(history) * 100

    @property
    def is_low_volatility(self) -> bool:
        return self.vol_percentile < self.hp['low_vol_percentile']

    @property
    def is_high_volatility(self) -> bool:
        return self.vol_percentile > self.hp['high_vol_percentile']

    @property
    def trend_direction(self) -> int:
        """Simple trend direction: 1 up, -1 down, 0 neutral"""
        ma = ta.sma(self.candles, period=20)
        if self.close > ma * 1.01:
            return 1
        elif self.close < ma * 0.99:
            return -1
        return 0

    def should_long(self) -> bool:
        # Low volatility with upward breakout (fear -> greed transition)
        prev_low_vol = self._was_low_volatility()
        return prev_low_vol and not self.is_low_volatility and self.trend_direction == 1

    def _was_low_volatility(self) -> bool:
        """Check if previous candle was in low volatility"""
        if len(self.candles) < self.hp['lookback'] + 2:
            return False
        prev_atr = ta.atr(self.candles[:-1], period=self.hp['atr_period'])
        history = self.atr_history[1:] if len(self.atr_history) > 1 else self.atr_history
        percentile = np.sum(history < prev_atr) / len(history) * 100
        return percentile < self.hp['low_vol_percentile']

    def should_short(self) -> bool:
        # High volatility spike with downward move (panic)
        return self.is_high_volatility and self.trend_direction == -1

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
        # Exit when volatility normalizes
        if self.is_long and self.vol_percentile > 50:
            self.liquidate()
        elif self.is_short and self.vol_percentile < 50:
            self.liquidate()
