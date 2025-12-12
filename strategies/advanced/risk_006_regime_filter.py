"""
RISK_006: Regime Filter Strategy
--------------------------------
Trade only in favorable market regimes.

Entry Long: Bullish regime with confirmation
Entry Short: Bearish regime with confirmation

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class RegimeFilter(Strategy):
    """Regime Filter Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "RISK_006"
        self.strategy_name = "Regime Filter"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 100, 'max': 250, 'default': 200},
            {'name': 'adx_threshold', 'type': int, 'min': 20, 'max': 30, 'default': 25},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _detect_regime(self) -> str:
        """Detect market regime"""
        ma = ta.sma(self.candles, period=self.hp['ma_period'])
        adx = ta.adx(self.candles, period=14)
        di = ta.di(self.candles, period=14)

        above_ma = self.close > ma
        strong_trend = adx > self.hp['adx_threshold']

        if above_ma and strong_trend and di[0] > di[1]:
            return "bullish_trend"
        elif not above_ma and strong_trend and di[1] > di[0]:
            return "bearish_trend"
        elif not strong_trend:
            return "ranging"
        else:
            return "mixed"

    @property
    def regime(self) -> str:
        return self._detect_regime()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def rsi(self) -> float:
        return ta.rsi(self.candles, period=14)

    def should_long(self) -> bool:
        # Only trade in bullish trend regime
        if self.regime != "bullish_trend":
            return False
        return self.rsi > 45 and self.rsi < 70

    def should_short(self) -> bool:
        # Only trade in bearish trend regime
        if self.regime != "bearish_trend":
            return False
        return self.rsi < 55 and self.rsi > 30

    def should_cancel_entry(self) -> bool:
        return self.regime in ["ranging", "mixed"]

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
        # Exit if regime changes
        if self.is_long and self.regime != "bullish_trend":
            self.liquidate()
        elif self.is_short and self.regime != "bearish_trend":
            self.liquidate()
