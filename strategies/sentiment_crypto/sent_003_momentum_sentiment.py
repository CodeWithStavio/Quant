"""
SENT_003: Momentum Sentiment Strategy
-------------------------------------
Use momentum as sentiment proxy.

Entry Long: Strong positive momentum (bullish sentiment)
Entry Short: Strong negative momentum (bearish sentiment)

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MomentumSentiment(Strategy):
    """Momentum-based Sentiment Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SENT_003"
        self.strategy_name = "Momentum Sentiment"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'roc_period', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'lookback', 'type': int, 'min': 40, 'max': 80, 'default': 50},
            {'name': 'threshold_percentile', 'type': float, 'min': 75, 'max': 90, 'default': 80},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def roc(self) -> float:
        return ta.roc(self.candles, period=self.hp['roc_period'])

    @property
    def roc_history(self) -> np.ndarray:
        """Get ROC history"""
        rocs = []
        for i in range(self.hp['lookback']):
            if len(self.candles) > i + self.hp['roc_period'] + 1:
                r = ta.roc(self.candles[:-(i+1)], period=self.hp['roc_period'])
                rocs.append(r)
        return np.array(rocs) if rocs else np.array([0])

    @property
    def momentum_percentile(self) -> float:
        """Current momentum percentile"""
        history = self.roc_history
        return np.sum(history < self.roc) / len(history) * 100

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.momentum_percentile > self.hp['threshold_percentile']

    def should_short(self) -> bool:
        return self.momentum_percentile < (100 - self.hp['threshold_percentile'])

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
        # Exit when momentum normalizes
        if self.is_long and self.momentum_percentile < 50:
            self.liquidate()
        elif self.is_short and self.momentum_percentile > 50:
            self.liquidate()
