"""
CRYPTO_001: Funding Rate Proxy Strategy
---------------------------------------
Simulate funding rate effects using price momentum.

Entry Long: Negative funding proxy (shorts overextended)
Entry Short: Positive funding proxy (longs overextended)

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 10/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class FundingRateProxy(Strategy):
    """Funding Rate Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_001"
        self.strategy_name = "Funding Rate Proxy"
        self.complexity = 6
        self.crypto_suitability = 10

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'extreme_threshold', 'type': float, 'min': 75, 'max': 90, 'default': 80},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_funding_proxy(self) -> float:
        """
        Proxy funding rate using premium indicator:
        High momentum = positive funding (longs pay shorts)
        Low momentum = negative funding (shorts pay longs)
        """
        lookback = self.hp['lookback']

        # Use momentum and RSI as funding proxy
        rsi = ta.rsi(self.candles, period=14)
        roc = ta.roc(self.candles, period=lookback)

        # Normalize to -100 to 100 scale
        funding_proxy = (rsi - 50) * 0.5 + roc * 2
        return np.clip(funding_proxy, -100, 100)

    def _get_funding_percentile(self) -> float:
        """Get historical percentile of funding proxy"""
        lookback = self.hp['lookback']
        current_funding = self._calculate_funding_proxy()

        funding_history = []
        for i in range(1, lookback * 2):
            if len(self.candles) > lookback + i:
                rsi = ta.rsi(self.candles[:-i], period=14)
                roc = ta.roc(self.candles[:-i], period=lookback)
                funding = (rsi - 50) * 0.5 + roc * 2
                funding_history.append(np.clip(funding, -100, 100))

        if not funding_history:
            return 50

        return np.sum(np.array(funding_history) < current_funding) / len(funding_history) * 100

    @property
    def funding_percentile(self) -> float:
        return self._get_funding_percentile()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Extreme negative funding = shorts overextended = long opportunity
        return self.funding_percentile < (100 - self.hp['extreme_threshold'])

    def should_short(self) -> bool:
        # Extreme positive funding = longs overextended = short opportunity
        return self.funding_percentile > self.hp['extreme_threshold']

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
        # Exit when funding normalizes
        if 40 < self.funding_percentile < 60:
            self.liquidate()
