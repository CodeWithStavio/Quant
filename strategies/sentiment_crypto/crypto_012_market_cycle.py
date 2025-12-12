"""
CRYPTO_012: Market Cycle Phase Strategy
---------------------------------------
Trade based on detected market cycle phases.

Entry Long: Recovery/expansion phase
Entry Short: Contraction/recession phase

Optimal Timeframes: 4h, 1d
Complexity: 7/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MarketCyclePhase(Strategy):
    """Market Cycle Phase Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_012"
        self.strategy_name = "Market Cycle Phase"
        self.complexity = 7
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 40, 'max': 80, 'default': 50},
            {'name': 'momentum_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'vol_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _get_trend_direction(self) -> int:
        """Get trend direction: 1 up, -1 down"""
        ma = ta.sma(self.candles, period=self.hp['ma_period'])
        prev_ma = ta.sma(self.candles[:-1], period=self.hp['ma_period'])
        if ma > prev_ma:
            return 1
        elif ma < prev_ma:
            return -1
        return 0

    def _get_momentum_direction(self) -> int:
        """Get momentum direction"""
        roc = ta.roc(self.candles, period=self.hp['momentum_period'])
        prev_roc = ta.roc(self.candles[:-1], period=self.hp['momentum_period'])
        if roc > prev_roc and roc > 0:
            return 1
        elif roc < prev_roc and roc < 0:
            return -1
        return 0

    def _detect_phase(self) -> str:
        """
        Detect cycle phase:
        - recovery: trend turning up, momentum improving
        - expansion: trend up, momentum strong
        - peak: trend up but momentum weakening
        - contraction: trend turning down, momentum declining
        - recession: trend down, momentum weak
        - trough: trend down but momentum improving
        """
        ma = ta.sma(self.candles, period=self.hp['ma_period'])
        trend = self._get_trend_direction()
        momentum = self._get_momentum_direction()
        roc = ta.roc(self.candles, period=self.hp['momentum_period'])

        above_ma = self.close > ma

        if above_ma and trend == 1 and momentum == 1:
            return "expansion"
        elif above_ma and trend == 1 and momentum != 1:
            return "peak"
        elif not above_ma and trend == -1 and momentum == -1:
            return "recession"
        elif not above_ma and trend == -1 and momentum != -1:
            return "trough"
        elif trend == 1 and roc > 0:
            return "recovery"
        elif trend == -1 and roc < 0:
            return "contraction"
        else:
            return "neutral"

    @property
    def phase(self) -> str:
        return self._detect_phase()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.phase in ["recovery", "expansion", "trough"]

    def should_short(self) -> bool:
        return self.phase in ["peak", "contraction"]

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
        if self.is_long and self.phase in ["peak", "contraction", "recession"]:
            self.liquidate()
        elif self.is_short and self.phase in ["trough", "recovery", "expansion"]:
            self.liquidate()
