"""
RISK_001: Volatility Adjusted Strategy
--------------------------------------
Adjust position size based on volatility.

Entry Long: Signal with volatility-adjusted sizing
Entry Short: Signal with volatility-adjusted sizing

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolatilityAdjusted(Strategy):
    """Volatility Adjusted Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "RISK_001"
        self.strategy_name = "Volatility Adjusted"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'base_risk', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'vol_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'target_vol', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
        ]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def current_volatility(self) -> float:
        """Calculate current volatility as daily return std"""
        returns = np.diff(self.candles[-self.hp['vol_lookback']:, 2]) / self.candles[-self.hp['vol_lookback']-1:-1, 2]
        return np.std(returns)

    @property
    def position_scalar(self) -> float:
        """Calculate position size scalar based on volatility"""
        target = self.hp['target_vol']
        current = self.current_volatility
        if current == 0:
            return 1.0
        return min(target / current, 2.0)  # Cap at 2x

    @property
    def adjusted_risk(self) -> float:
        return self.hp['base_risk'] * self.position_scalar

    @property
    def trend(self) -> int:
        ma = ta.sma(self.candles, period=20)
        if self.close > ma:
            return 1
        elif self.close < ma:
            return -1
        return 0

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    def should_long(self) -> bool:
        return self.trend == 1 and self.rsi > 40 and self.rsi < 70

    def should_short(self) -> bool:
        return self.trend == -1 and self.rsi < 60 and self.rsi > 30

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = entry - (self.atr * 2)
        qty = utils.size_to_qty(self.balance * self.adjusted_risk, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = entry + (self.atr * 2)
        qty = utils.size_to_qty(self.balance * self.adjusted_risk, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()
