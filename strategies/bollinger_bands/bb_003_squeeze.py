"""
BB_003: Bollinger Band Squeeze Strategy
---------------------------------------
Trade when BB contracts (squeeze) then expands (breakout).
Uses BB Width to identify squeeze conditions.

Entry: When bandwidth is at N-period low, prepare for breakout direction

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class BBSqueeze(Strategy):
    """Bollinger Band Squeeze Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BB_003"
        self.strategy_name = "BB Squeeze"
        self.complexity = 5
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'bb_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'bb_std', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'squeeze_lookback', 'type': int, 'min': 50, 'max': 150, 'default': 100},
            {'name': 'squeeze_threshold', 'type': float, 'min': 0.1, 'max': 0.3, 'default': 0.2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 3.0, 'max': 6.0, 'default': 4.0},
        ]

    def _get_bb_width(self, candles=None) -> np.ndarray:
        """Calculate BB Width = (Upper - Lower) / Middle"""
        if candles is None:
            candles = self.candles

        upper, middle, lower = ta.bollinger_bands(
            candles,
            period=self.hp['bb_period'],
            devup=self.hp['bb_std'],
            devdn=self.hp['bb_std'],
            sequential=True
        )

        width = np.zeros(len(middle))
        for i in range(len(middle)):
            if middle[i] != 0:
                width[i] = (upper[i] - lower[i]) / middle[i]

        return width

    @property
    def bb_width(self) -> float:
        return self._get_bb_width()[-1]

    @property
    def bb_width_min(self) -> float:
        """Minimum width over lookback period"""
        width = self._get_bb_width()
        lookback = self.hp['squeeze_lookback']
        return np.min(width[-lookback:])

    def _in_squeeze(self) -> bool:
        """Check if currently in squeeze"""
        return self.bb_width <= self.bb_width_min * (1 + self.hp['squeeze_threshold'])

    def _squeeze_fire_up(self) -> bool:
        """Squeeze fired with upward breakout"""
        width = self._get_bb_width()
        # Width was at minimum, now expanding
        was_squeeze = width[-2] <= self.bb_width_min * (1 + self.hp['squeeze_threshold'])
        expanding = width[-1] > width[-2]
        # Price breaking up
        upper, middle, lower = ta.bollinger_bands(
            self.candles,
            period=self.hp['bb_period'],
            devup=self.hp['bb_std'],
            devdn=self.hp['bb_std']
        )
        price_breaking_up = self.close > middle and self.close > self.candles[-2, 2]
        return was_squeeze and expanding and price_breaking_up

    def _squeeze_fire_down(self) -> bool:
        """Squeeze fired with downward breakout"""
        width = self._get_bb_width()
        was_squeeze = width[-2] <= self.bb_width_min * (1 + self.hp['squeeze_threshold'])
        expanding = width[-1] > width[-2]
        # Price breaking down
        upper, middle, lower = ta.bollinger_bands(
            self.candles,
            period=self.hp['bb_period'],
            devup=self.hp['bb_std'],
            devdn=self.hp['bb_std']
        )
        price_breaking_down = self.close < middle and self.close < self.candles[-2, 2]
        return was_squeeze and expanding and price_breaking_down

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._squeeze_fire_up()

    def should_short(self) -> bool:
        return self._squeeze_fire_down()

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
        pass
