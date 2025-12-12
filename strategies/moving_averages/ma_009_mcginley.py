"""
MA_009: McGinley Dynamic Indicator Strategy
-------------------------------------------
Self-adjusting MA that automatically adjusts speed based on market conditions.

McGinley = MD[1] + (Price - MD[1]) / (N * (Price/MD[1])^4)

Entry Long: Price crosses above McGinley when trending up
Entry Short: Price crosses below McGinley when trending down

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class McGinleyStrategy(Strategy):
    """McGinley Dynamic Indicator Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_009"
        self.strategy_name = "McGinley Dynamic"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 10, 'max': 30, 'default': 14},
            {'name': 'k', 'type': float, 'min': 0.5, 'max': 1.0, 'default': 0.6},
            {'name': 'slope_lookback', 'type': int, 'min': 3, 'max': 10, 'default': 5},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 2.5},
        ]

    def _calculate_mcginley(self, candles=None) -> np.ndarray:
        """Calculate McGinley Dynamic (sequential)"""
        if candles is None:
            candles = self.candles

        close = candles[:, 2]
        n = self.hp['period']
        k = self.hp['k']

        md = np.zeros(len(close))
        md[0] = close[0]

        for i in range(1, len(close)):
            if md[i-1] == 0:
                md[i] = close[i]
            else:
                ratio = close[i] / md[i-1]
                md[i] = md[i-1] + (close[i] - md[i-1]) / (k * n * (ratio ** 4))

        return md

    @property
    def mcginley(self) -> float:
        return self._calculate_mcginley()[-1]

    @property
    def mcginley_prev(self) -> float:
        return self._calculate_mcginley()[-2]

    @property
    def mcginley_slope(self) -> float:
        md = self._calculate_mcginley()
        lookback = self.hp['slope_lookback']
        return md[-1] - md[-lookback]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _price_crossed_above(self) -> bool:
        md = self._calculate_mcginley()
        return self.candles[-2, 2] <= md[-2] and self.candles[-1, 2] > md[-1]

    def _price_crossed_below(self) -> bool:
        md = self._calculate_mcginley()
        return self.candles[-2, 2] >= md[-2] and self.candles[-1, 2] < md[-1]

    def should_long(self) -> bool:
        return self._price_crossed_above() and self.mcginley_slope > 0

    def should_short(self) -> bool:
        return self._price_crossed_below() and self.mcginley_slope < 0

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
        # Exit when price crosses back or slope reverses
        if self.is_long:
            if self._price_crossed_below() or self.mcginley_slope < 0:
                self.liquidate()
        elif self.is_short:
            if self._price_crossed_above() or self.mcginley_slope > 0:
                self.liquidate()
