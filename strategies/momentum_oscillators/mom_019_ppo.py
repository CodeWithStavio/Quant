"""
MOM_019: Percentage Price Oscillator (PPO) Strategy
---------------------------------------------------
PPO is MACD expressed as percentage - better for comparing different assets.
PPO = ((Fast EMA - Slow EMA) / Slow EMA) * 100

Entry Long: PPO crosses above signal line
Entry Short: PPO crosses below signal line

Optimal Timeframes: 15m, 1h, 4h
Complexity: 3/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class PPOStrategy(Strategy):
    """Percentage Price Oscillator Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MOM_019"
        self.strategy_name = "PPO"
        self.complexity = 3
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'fast_period', 'type': int, 'min': 8, 'max': 15, 'default': 12},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 30, 'default': 26},
            {'name': 'signal_period', 'type': int, 'min': 7, 'max': 12, 'default': 9},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    def _calculate_ppo(self, candles=None) -> tuple:
        """Calculate PPO and Signal"""
        if candles is None:
            candles = self.candles

        fast_ema = ta.ema(candles, period=self.hp['fast_period'], sequential=True)
        slow_ema = ta.ema(candles, period=self.hp['slow_period'], sequential=True)

        # PPO = ((Fast - Slow) / Slow) * 100
        ppo = np.zeros(len(fast_ema))
        for i in range(len(fast_ema)):
            if slow_ema[i] != 0:
                ppo[i] = ((fast_ema[i] - slow_ema[i]) / slow_ema[i]) * 100

        # Signal line
        alpha = 2 / (self.hp['signal_period'] + 1)
        signal = np.zeros(len(ppo))
        signal[0] = ppo[0]
        for i in range(1, len(ppo)):
            signal[i] = alpha * ppo[i] + (1 - alpha) * signal[i-1]

        return ppo[-1], signal[-1]

    @property
    def ppo(self) -> float:
        ppo, signal = self._calculate_ppo()
        return ppo

    @property
    def ppo_signal(self) -> float:
        ppo, signal = self._calculate_ppo()
        return signal

    @property
    def ppo_prev(self) -> float:
        ppo, signal = self._calculate_ppo(self.candles[:-1])
        return ppo

    @property
    def ppo_signal_prev(self) -> float:
        ppo, signal = self._calculate_ppo(self.candles[:-1])
        return signal

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.ppo_prev <= self.ppo_signal_prev and self.ppo > self.ppo_signal

    def should_short(self) -> bool:
        return self.ppo_prev >= self.ppo_signal_prev and self.ppo < self.ppo_signal

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
        if self.is_long and self.ppo < self.ppo_signal:
            self.liquidate()
        elif self.is_short and self.ppo > self.ppo_signal:
            self.liquidate()
