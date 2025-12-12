"""
ML_011: Statistical Arbitrage Strategy
--------------------------------------
Trade mean reversion based on statistical analysis.

Entry Long: Price significantly below statistical fair value
Entry Short: Price significantly above statistical fair value

Optimal Timeframes: 1h, 4h
Complexity: 7/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class StatisticalArbitrage(Strategy):
    """Statistical Arbitrage Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_011"
        self.strategy_name = "Statistical Arbitrage"
        self.complexity = 7
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 40, 'max': 80, 'default': 60},
            {'name': 'entry_zscore', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'exit_zscore', 'type': float, 'min': 0.3, 'max': 0.7, 'default': 0.5},
            {'name': 'half_life_max', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_half_life(self) -> float:
        """Calculate mean reversion half-life using OLS"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]

        # Lag regression: price_diff = alpha + beta * lagged_price + error
        lagged = prices[:-1]
        diff = np.diff(prices)

        if len(lagged) < 2:
            return float('inf')

        # Simple OLS
        x = lagged - np.mean(lagged)
        y = diff

        beta = np.sum(x * y) / np.sum(x * x) if np.sum(x * x) != 0 else 0

        if beta >= 0:
            return float('inf')  # Not mean reverting

        # Half-life = -ln(2) / beta
        half_life = -np.log(2) / beta
        return half_life

    @property
    def half_life(self) -> float:
        return self._calculate_half_life()

    @property
    def is_mean_reverting(self) -> bool:
        return 0 < self.half_life < self.hp['half_life_max']

    @property
    def fair_value(self) -> float:
        """Rolling mean as fair value"""
        return np.mean(self.candles[-self.hp['lookback']:, 2])

    @property
    def zscore(self) -> float:
        """Calculate z-score from fair value"""
        prices = self.candles[-self.hp['lookback']:, 2]
        std = np.std(prices)
        if std == 0:
            return 0
        return (self.close - self.fair_value) / std

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.is_mean_reverting and self.zscore < -self.hp['entry_zscore']

    def should_short(self) -> bool:
        return self.is_mean_reverting and self.zscore > self.hp['entry_zscore']

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * self.hp['atr_multiplier_sl'])
        target = self.fair_value
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * self.hp['atr_multiplier_sl'])
        target = self.fair_value
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        # Exit when z-score normalizes
        if self.is_long and self.zscore > -self.hp['exit_zscore']:
            self.liquidate()
        elif self.is_short and self.zscore < self.hp['exit_zscore']:
            self.liquidate()
