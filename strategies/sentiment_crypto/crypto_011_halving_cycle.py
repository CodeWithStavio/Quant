"""
CRYPTO_011: Halving Cycle Proxy Strategy
----------------------------------------
Trade based on market cycle phases using momentum.

Entry Long: Early/mid bull cycle (strong momentum)
Entry Short: Late bull/bear cycle (weakening momentum)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 10/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class HalvingCycleProxy(Strategy):
    """Halving Cycle Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_011"
        self.strategy_name = "Halving Cycle Proxy"
        self.complexity = 6
        self.crypto_suitability = 10

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'long_period', 'type': int, 'min': 100, 'max': 200, 'default': 150},
            {'name': 'short_period', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'momentum_threshold', 'type': float, 'min': 10, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.5, 'default': 2.5},
        ]

    def _detect_cycle_phase(self) -> str:
        """
        Detect market cycle phase:
        - accumulation: Low momentum, low volatility
        - early_bull: Rising momentum, price above long MA
        - mid_bull: Strong momentum, trending up
        - late_bull: High momentum, overbought signals
        - distribution: Declining momentum at highs
        - bear: Price below long MA, negative momentum
        """
        long_ma = ta.sma(self.candles, period=self.hp['long_period'])
        short_ma = ta.sma(self.candles, period=self.hp['short_period'])
        rsi = ta.rsi(self.candles, period=14)
        roc = ta.roc(self.candles, period=self.hp['short_period'])

        above_long_ma = self.close > long_ma
        above_short_ma = self.close > short_ma
        strong_momentum = roc > self.hp['momentum_threshold']
        weak_momentum = roc < self.hp['momentum_threshold'] / 2

        if not above_long_ma and weak_momentum and rsi < 40:
            return "accumulation"
        elif above_long_ma and above_short_ma and strong_momentum and rsi < 70:
            return "early_bull"
        elif above_long_ma and strong_momentum and 50 < rsi < 75:
            return "mid_bull"
        elif above_long_ma and rsi > 75:
            return "late_bull"
        elif above_long_ma and not strong_momentum and rsi > 60:
            return "distribution"
        else:
            return "bear"

    @property
    def cycle_phase(self) -> str:
        return self._detect_cycle_phase()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Enter during early or mid bull phases
        return self.cycle_phase in ["early_bull", "mid_bull", "accumulation"]

    def should_short(self) -> bool:
        # Enter during late bull (distribution) or bear phases
        return self.cycle_phase in ["late_bull", "distribution"]

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
        # Exit on phase change
        if self.is_long and self.cycle_phase in ["late_bull", "distribution", "bear"]:
            self.liquidate()
        elif self.is_short and self.cycle_phase in ["early_bull", "mid_bull"]:
            self.liquidate()
