"""
COMBO_005: Pivot + Momentum Combo Strategy
------------------------------------------
Combine pivot levels with momentum confirmation.

Entry Long: Bounce off pivot support + Positive momentum
Entry Short: Rejection at pivot resistance + Negative momentum

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class PivotMomentumCombo(Strategy):
    """Pivot + Momentum Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "COMBO_005"
        self.strategy_name = "Pivot Momentum Combo"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'pivot_lookback', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'mom_period', 'type': int, 'min': 8, 'max': 15, 'default': 10},
            {'name': 'touch_tolerance', 'type': float, 'min': 0.2, 'max': 0.5, 'default': 0.3},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_pivots(self) -> dict:
        """Calculate pivot levels"""
        lookback = self.hp['pivot_lookback']
        high = np.max(self.candles[-lookback:-1, 3])
        low = np.min(self.candles[-lookback:-1, 4])
        close = self.candles[-2, 2]

        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high

        return {'pivot': pivot, 'r1': r1, 's1': s1}

    @property
    def pivots(self) -> dict:
        return self._calculate_pivots()

    @property
    def momentum(self) -> float:
        return ta.roc(self.candles, period=self.hp['mom_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _near_support(self) -> bool:
        tolerance = self.atr * self.hp['touch_tolerance']
        return abs(self.low - self.pivots['s1']) < tolerance

    def _near_resistance(self) -> bool:
        tolerance = self.atr * self.hp['touch_tolerance']
        return abs(self.high - self.pivots['r1']) < tolerance

    def should_long(self) -> bool:
        near_support = self._near_support()
        positive_mom = self.momentum > 0
        bullish_candle = self.close > self.open

        return near_support and positive_mom and bullish_candle

    def should_short(self) -> bool:
        near_resistance = self._near_resistance()
        negative_mom = self.momentum < 0
        bearish_candle = self.close < self.open

        return near_resistance and negative_mom and bearish_candle

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.pivots['s1'] - (self.atr * 0.5)
        target = self.pivots['pivot']
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def go_short(self):
        entry = self.price
        stop = self.pivots['r1'] + (self.atr * 0.5)
        target = self.pivots['pivot']
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, target

    def update_position(self):
        if self.is_long and self.momentum < -1:
            self.liquidate()
        elif self.is_short and self.momentum > 1:
            self.liquidate()
