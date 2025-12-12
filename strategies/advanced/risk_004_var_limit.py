"""
RISK_004: VaR Limit Strategy
----------------------------
Position sizing based on Value at Risk.

Entry Long: Signal with VaR-limited position
Entry Short: Signal with VaR-limited position

Optimal Timeframes: 4h, 1d
Complexity: 7/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VaRLimit(Strategy):
    """VaR Limit Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "RISK_004"
        self.strategy_name = "VaR Limit"
        self.complexity = 7
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'var_limit', 'type': float, 'min': 0.02, 'max': 0.05, 'default': 0.03},
            {'name': 'confidence', 'type': float, 'min': 0.95, 'max': 0.99, 'default': 0.95},
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 100, 'default': 50},
        ]

    def _calculate_var(self) -> float:
        """Calculate historical VaR"""
        lookback = self.hp['lookback']
        returns = np.diff(self.candles[-lookback:, 2]) / self.candles[-lookback-1:-1, 2]

        # Parametric VaR using normal distribution
        mean = np.mean(returns)
        std = np.std(returns)

        # Z-score for confidence level
        z_scores = {0.95: 1.645, 0.99: 2.326}
        z = z_scores.get(self.hp['confidence'], 1.645)

        # VaR (positive value = potential loss)
        var = -(mean - z * std)
        return max(var, 0.01)  # Minimum 1%

    @property
    def var(self) -> float:
        return self._calculate_var()

    @property
    def max_position(self) -> float:
        """Maximum position size based on VaR limit"""
        if self.var == 0:
            return 0.02
        # Position size = VaR limit / individual VaR
        return min(self.hp['var_limit'] / self.var, 0.1)

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
        rsi = ta.rsi(self.candles, period=14)
        return self.trend == 1 and rsi < 70

    def should_short(self) -> bool:
        rsi = ta.rsi(self.candles, period=14)
        return self.trend == -1 and rsi > 30

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * self.max_position, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * 2)
        qty = utils.size_to_qty(self.balance * self.max_position, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()
