"""
BB_005: Double Bollinger Bands Strategy
---------------------------------------
Two sets of Bollinger Bands (1 and 2 std dev) for zone trading.

Entry Long: Price in lower zone (between -1 and -2 std)
Entry Short: Price in upper zone (between +1 and +2 std)

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class DoubleBB(Strategy):
    """Double Bollinger Bands Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "BB_005"
        self.strategy_name = "Double BB"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'inner_std', 'type': float, 'min': 0.5, 'max': 1.5, 'default': 1.0},
            {'name': 'outer_std', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 2.5, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
        ]

    def _get_inner_bb(self):
        return ta.bollinger_bands(
            self.candles,
            period=self.hp['period'],
            devup=self.hp['inner_std'],
            devdn=self.hp['inner_std']
        )

    def _get_outer_bb(self):
        return ta.bollinger_bands(
            self.candles,
            period=self.hp['period'],
            devup=self.hp['outer_std'],
            devdn=self.hp['outer_std']
        )

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _in_buy_zone(self) -> bool:
        """Price between inner lower and outer lower"""
        inner_upper, inner_middle, inner_lower = self._get_inner_bb()
        outer_upper, outer_middle, outer_lower = self._get_outer_bb()
        return outer_lower <= self.close <= inner_lower

    def _in_sell_zone(self) -> bool:
        """Price between inner upper and outer upper"""
        inner_upper, inner_middle, inner_lower = self._get_inner_bb()
        outer_upper, outer_middle, outer_lower = self._get_outer_bb()
        return inner_upper <= self.close <= outer_upper

    def _bullish_candle(self) -> bool:
        return self.close > self.open

    def _bearish_candle(self) -> bool:
        return self.close < self.open

    def should_long(self) -> bool:
        return self._in_buy_zone() and self._bullish_candle()

    def should_short(self) -> bool:
        return self._in_sell_zone() and self._bearish_candle()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        outer_upper, outer_middle, outer_lower = self._get_outer_bb()
        stop = outer_lower - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        inner_upper, inner_middle, inner_lower = self._get_inner_bb()
        self.take_profit = [
            (0.5, inner_middle),
            (0.5, inner_upper),
        ]

    def go_short(self):
        entry = self.price
        outer_upper, outer_middle, outer_lower = self._get_outer_bb()
        stop = outer_upper + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        inner_upper, inner_middle, inner_lower = self._get_inner_bb()
        self.take_profit = [
            (0.5, inner_middle),
            (0.5, inner_lower),
        ]

    def update_position(self):
        pass
