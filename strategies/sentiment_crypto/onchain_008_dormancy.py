"""
ONCHAIN_008: Dormancy Proxy Strategy
------------------------------------
Simulate dormancy through price stability metrics.

Entry Long: Low dormancy activity (stable accumulation phase)
Entry Short: High dormancy break (old coins moving)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DormancyProxy(Strategy):
    """Dormancy Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ONCHAIN_008"
        self.strategy_name = "Dormancy Proxy"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 60, 'default': 40},
            {'name': 'stability_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'volatility_threshold', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_dormancy_score(self) -> float:
        """Calculate dormancy proxy (stability = dormancy)"""
        period = self.hp['stability_period']
        prices = self.candles[-period:, 2]
        returns = np.diff(prices) / prices[:-1]

        # Low volatility = high dormancy (coins not moving)
        volatility = np.std(returns) * 100
        return 1 / (volatility + 0.1)  # Inverse: high stability = high dormancy

    def _get_dormancy_percentile(self) -> float:
        """Get current dormancy percentile"""
        lookback = self.hp['lookback']
        current_dormancy = self._calculate_dormancy_score()

        dormancy_history = []
        period = self.hp['stability_period']
        for i in range(1, lookback):
            if len(self.candles) > period + i:
                prices = self.candles[-period-i:-i, 2]
                returns = np.diff(prices) / prices[:-1]
                vol = np.std(returns) * 100
                dormancy_history.append(1 / (vol + 0.1))

        if not dormancy_history:
            return 50

        return np.sum(np.array(dormancy_history) < current_dormancy) / len(dormancy_history) * 100

    def _is_dormancy_break(self) -> bool:
        """Detect when dormancy breaks (old coins start moving)"""
        lookback = self.hp['lookback']

        # Compare recent volatility to historical
        recent_vol = np.std(np.diff(self.candles[-10:, 2]) / self.candles[-10:-1, 2])
        hist_vol = np.std(np.diff(self.candles[-lookback:-10, 2]) / self.candles[-lookback:-11, 2])

        return recent_vol > hist_vol * self.hp['volatility_threshold']

    @property
    def dormancy_percentile(self) -> float:
        return self._get_dormancy_percentile()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def trend(self) -> int:
        ma = ta.sma(self.candles, period=20)
        if self.close > ma:
            return 1
        elif self.close < ma:
            return -1
        return 0

    def should_long(self) -> bool:
        # High dormancy (accumulation) with upward trend
        high_dormancy = self.dormancy_percentile > 70
        return high_dormancy and self.trend == 1

    def should_short(self) -> bool:
        # Dormancy break with downward move
        return self._is_dormancy_break() and self.trend == -1

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
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()
