"""
TF_008: Ichimoku Trend Strategy
-------------------------------
Trade based on Ichimoku Cloud for trend direction.

Entry Long: Price above cloud with bullish TK cross
Entry Short: Price below cloud with bearish TK cross

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class IchimokuTrend(Strategy):
    """Ichimoku Trend Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "TF_008"
        self.strategy_name = "Ichimoku Trend"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'tenkan', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'kijun', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'senkou_b', 'type': int, 'min': 45, 'max': 60, 'default': 52},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def ichimoku(self):
        return ta.ichimoku_cloud(self.candles,
                                  conversion_line_period=self.hp['tenkan'],
                                  base_line_period=self.hp['kijun'],
                                  lagging_line_period=self.hp['kijun'],
                                  displacement=self.hp['kijun'])

    @property
    def tenkan_sen(self) -> float:
        return self.ichimoku[0]

    @property
    def kijun_sen(self) -> float:
        return self.ichimoku[1]

    @property
    def senkou_a(self) -> float:
        return self.ichimoku[2]

    @property
    def senkou_b(self) -> float:
        return self.ichimoku[3]

    @property
    def cloud_top(self) -> float:
        return max(self.senkou_a, self.senkou_b)

    @property
    def cloud_bottom(self) -> float:
        return min(self.senkou_a, self.senkou_b)

    @property
    def above_cloud(self) -> bool:
        return self.close > self.cloud_top

    @property
    def below_cloud(self) -> bool:
        return self.close < self.cloud_bottom

    @property
    def bullish_tk_cross(self) -> bool:
        prev_ich = ta.ichimoku_cloud(self.candles[:-1],
                                       conversion_line_period=self.hp['tenkan'],
                                       base_line_period=self.hp['kijun'],
                                       lagging_line_period=self.hp['kijun'],
                                       displacement=self.hp['kijun'])
        prev_tenkan = prev_ich[0]
        prev_kijun = prev_ich[1]
        return prev_tenkan <= prev_kijun and self.tenkan_sen > self.kijun_sen

    @property
    def bearish_tk_cross(self) -> bool:
        prev_ich = ta.ichimoku_cloud(self.candles[:-1],
                                       conversion_line_period=self.hp['tenkan'],
                                       base_line_period=self.hp['kijun'],
                                       lagging_line_period=self.hp['kijun'],
                                       displacement=self.hp['kijun'])
        prev_tenkan = prev_ich[0]
        prev_kijun = prev_ich[1]
        return prev_tenkan >= prev_kijun and self.tenkan_sen < self.kijun_sen

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.above_cloud and self.bullish_tk_cross

    def should_short(self) -> bool:
        return self.below_cloud and self.bearish_tk_cross

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.kijun_sen - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.buy = qty, entry
        self.stop_loss = qty, stop

    def go_short(self):
        entry = self.price
        stop = self.kijun_sen + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)
        self.sell = qty, entry
        self.stop_loss = qty, stop

    def update_position(self):
        # Exit on cloud entry or TK cross reversal
        if self.is_long:
            if self.below_cloud or self.bearish_tk_cross:
                self.liquidate()
        elif self.is_short:
            if self.above_cloud or self.bullish_tk_cross:
                self.liquidate()
