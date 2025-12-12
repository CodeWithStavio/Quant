"""
MOM_016: Coppock Curve Strategy
-------------------------------
Long-term momentum indicator designed for monthly charts but adaptable.
Coppock = WMA(ROC(14) + ROC(11), 10)

Entry Long: Coppock crosses above 0 from negative territory
Entry Short: Coppock crosses below 0 from positive territory

Optimal Timeframes: 4h, 1d
Complexity: 4/10
Crypto Suitability: 6/10 (better for longer timeframes)
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class CoppockCurve(Strategy):
    """Coppock Curve Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_016"
        self.strategy_name = "Coppock Curve"
        self.complexity = 4
        self.crypto_suitability = 6

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'roc_period1', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'roc_period2', 'type': int, 'min': 8, 'max': 15, 'default': 11},
            {'name': 'wma_period', 'type': int, 'min': 5, 'max': 15, 'default': 10},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 4.0, 'default': 2.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 6.0, 'default': 4.0},
        ]

    def _calculate_roc(self, close: np.ndarray, period: int) -> np.ndarray:
        """Calculate Rate of Change"""
        roc = np.zeros(len(close))
        for i in range(period, len(close)):
            if close[i-period] != 0:
                roc[i] = ((close[i] - close[i-period]) / close[i-period]) * 100
        return roc

    def _calculate_wma(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Weighted Moving Average"""
        weights = np.arange(1, period + 1)
        wma = np.zeros(len(data))
        for i in range(period - 1, len(data)):
            wma[i] = np.sum(data[i-period+1:i+1] * weights) / np.sum(weights)
        return wma

    def _calculate_coppock(self, candles=None) -> np.ndarray:
        """Calculate Coppock Curve"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]
        roc1 = self._calculate_roc(close, self.hp['roc_period1'])
        roc2 = self._calculate_roc(close, self.hp['roc_period2'])

        combined_roc = roc1 + roc2
        coppock = self._calculate_wma(combined_roc, self.hp['wma_period'])

        return coppock

    @property
    def coppock(self) -> float:
        return self._calculate_coppock()[-1]

    @property
    def coppock_prev(self) -> float:
        return self._calculate_coppock()[-2]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Coppock crosses above 0 from negative
        return self.coppock_prev <= 0 and self.coppock > 0

    def should_short(self) -> bool:
        # Coppock crosses below 0 from positive
        return self.coppock_prev >= 0 and self.coppock < 0

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
        if self.is_long and self.coppock < 0:
            self.liquidate()
        elif self.is_short and self.coppock > 0:
            self.liquidate()
