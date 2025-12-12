"""
CRYPTO_006: Volatility Regime Strategy
--------------------------------------
Trade based on volatility regime changes.

Entry Long: Low to high volatility transition (breakout)
Entry Short: High volatility exhaustion (reversal)

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolatilityRegime(Strategy):
    """Volatility Regime Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_006"
        self.strategy_name = "Volatility Regime"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'atr_period', 'type': int, 'min': 10, 'max': 20, 'default': 14},
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 60, 'default': 40},
            {'name': 'low_vol_pct', 'type': float, 'min': 20, 'max': 35, 'default': 25},
            {'name': 'high_vol_pct', 'type': float, 'min': 75, 'max': 90, 'default': 80},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=self.hp['atr_period'])

    @property
    def prev_atr(self) -> float:
        return ta.atr(self.candles[:-1], period=self.hp['atr_period'])

    def _get_vol_percentile(self) -> float:
        """Get volatility percentile"""
        lookback = self.hp['lookback']
        current_atr = self.atr

        atr_history = []
        for i in range(1, lookback):
            if len(self.candles) > i + self.hp['atr_period']:
                atr_history.append(ta.atr(self.candles[:-i], period=self.hp['atr_period']))

        if not atr_history:
            return 50

        return np.sum(np.array(atr_history) < current_atr) / len(atr_history) * 100

    def _get_prev_vol_percentile(self) -> float:
        """Get previous volatility percentile"""
        lookback = self.hp['lookback']
        prev_atr = self.prev_atr

        atr_history = []
        for i in range(2, lookback + 1):
            if len(self.candles) > i + self.hp['atr_period']:
                atr_history.append(ta.atr(self.candles[:-i], period=self.hp['atr_period']))

        if not atr_history:
            return 50

        return np.sum(np.array(atr_history) < prev_atr) / len(atr_history) * 100

    @property
    def vol_percentile(self) -> float:
        return self._get_vol_percentile()

    @property
    def prev_vol_percentile(self) -> float:
        return self._get_prev_vol_percentile()

    @property
    def trend(self) -> int:
        ma = ta.sma(self.candles, period=20)
        return 1 if self.close > ma else -1

    def should_long(self) -> bool:
        # Transition from low to high volatility with uptrend
        low_to_high = (self.prev_vol_percentile < self.hp['low_vol_pct'] and
                       self.vol_percentile > self.hp['low_vol_pct'])
        return low_to_high and self.trend == 1

    def should_short(self) -> bool:
        # High volatility exhaustion with downtrend
        exhaustion = (self.prev_vol_percentile > self.hp['high_vol_pct'] and
                      self.vol_percentile < self.hp['high_vol_pct'])
        return exhaustion and self.trend == -1

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
        # Exit on trend reversal
        if self.is_long and self.trend == -1:
            self.liquidate()
        elif self.is_short and self.trend == 1:
            self.liquidate()
