"""
ML_008: Ensemble Signals Strategy
---------------------------------
Combine signals from multiple strategies for robustness.

Entry Long: Majority of sub-strategies signal long
Entry Short: Majority of sub-strategies signal short

Optimal Timeframes: 1h, 4h
Complexity: 7/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class EnsembleSignals(Strategy):
    """Ensemble Signals Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ML_008"
        self.strategy_name = "Ensemble Signals"
        self.complexity = 7
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'agreement_threshold', 'type': int, 'min': 3, 'max': 5, 'default': 4},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _ma_crossover_signal(self) -> int:
        """MA crossover strategy signal"""
        fast = ta.ema(self.candles, period=10)
        slow = ta.ema(self.candles, period=20)
        prev_fast = ta.ema(self.candles[:-1], period=10)
        prev_slow = ta.ema(self.candles[:-1], period=20)

        if prev_fast <= prev_slow and fast > slow:
            return 1
        elif prev_fast >= prev_slow and fast < slow:
            return -1
        return 0

    def _rsi_reversal_signal(self) -> int:
        """RSI reversal strategy signal"""
        rsi = ta.rsi(self.candles, period=14)
        prev_rsi = ta.rsi(self.candles[:-1], period=14)

        if prev_rsi < 30 and rsi > 30:
            return 1
        elif prev_rsi > 70 and rsi < 70:
            return -1
        return 0

    def _bollinger_signal(self) -> int:
        """Bollinger band strategy signal"""
        bb = ta.bollinger_bands(self.candles, period=20, devup=2, devdn=2)
        if self.low <= bb[2] and self.close > self.open:
            return 1
        elif self.high >= bb[0] and self.close < self.open:
            return -1
        return 0

    def _momentum_signal(self) -> int:
        """Momentum strategy signal"""
        mom = ta.roc(self.candles, period=10)
        prev_mom = ta.roc(self.candles[:-1], period=10)

        if prev_mom < 0 and mom > 0:
            return 1
        elif prev_mom > 0 and mom < 0:
            return -1
        return 0

    def _trend_signal(self) -> int:
        """Trend following signal"""
        adx = ta.adx(self.candles, period=14)
        di_plus = ta.di(self.candles, period=14)[0]
        di_minus = ta.di(self.candles, period=14)[1]

        if adx > 25:
            if di_plus > di_minus:
                return 1
            else:
                return -1
        return 0

    def _volume_signal(self) -> int:
        """Volume confirmation signal"""
        avg_vol = np.mean(self.candles[-20:-1, 5])
        curr_vol = self.candles[-1, 5]

        if curr_vol > avg_vol * 1.5:
            if self.close > self.open:
                return 1
            elif self.close < self.open:
                return -1
        return 0

    def _get_ensemble_signal(self) -> int:
        """Aggregate all signals"""
        signals = [
            self._ma_crossover_signal(),
            self._rsi_reversal_signal(),
            self._bollinger_signal(),
            self._momentum_signal(),
            self._trend_signal(),
            self._volume_signal(),
        ]

        long_votes = sum(1 for s in signals if s > 0)
        short_votes = sum(1 for s in signals if s < 0)

        if long_votes >= self.hp['agreement_threshold']:
            return 1
        elif short_votes >= self.hp['agreement_threshold']:
            return -1
        return 0

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._get_ensemble_signal() == 1

    def should_short(self) -> bool:
        return self._get_ensemble_signal() == -1

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
        signal = self._get_ensemble_signal()
        if self.is_long and signal < 0:
            self.liquidate()
        elif self.is_short and signal > 0:
            self.liquidate()
