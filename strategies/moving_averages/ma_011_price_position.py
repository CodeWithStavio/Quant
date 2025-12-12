"""
MA_011: MA Price Position Strategy
----------------------------------
Trade pullbacks to moving average in established trends.

Entry Long: Price above MA in uptrend, pullback touches/approaches MA
Entry Short: Price below MA in downtrend, rally touches/approaches MA

Optimal Timeframes: 15m, 1h, 4h
Complexity: 4/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MAPricePosition(Strategy):
    """MA Price Position Strategy - Pullback Trading"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_011"
        self.strategy_name = "MA Price Position"
        self.complexity = 4
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 50, 'default': 21},
            {'name': 'trend_period', 'type': int, 'min': 50, 'max': 200, 'default': 100},
            {'name': 'pullback_threshold', 'type': float, 'min': 0.001, 'max': 0.02, 'default': 0.005},
            {'name': 'trend_strength_bars', 'type': int, 'min': 5, 'max': 20, 'default': 10},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.0, 'max': 5.0, 'default': 3.0},
        ]

    @property
    def signal_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ma_period'])

    @property
    def trend_ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['trend_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _is_uptrend(self) -> bool:
        """Check if in strong uptrend"""
        # Price above trend MA
        if self.close <= self.trend_ma:
            return False

        # Check MA is rising
        ma_seq = ta.ema(self.candles, period=self.hp['trend_period'], sequential=True)
        bars = self.hp['trend_strength_bars']
        return all(ma_seq[-i] > ma_seq[-i-1] for i in range(1, bars))

    def _is_downtrend(self) -> bool:
        """Check if in strong downtrend"""
        # Price below trend MA
        if self.close >= self.trend_ma:
            return False

        # Check MA is falling
        ma_seq = ta.ema(self.candles, period=self.hp['trend_period'], sequential=True)
        bars = self.hp['trend_strength_bars']
        return all(ma_seq[-i] < ma_seq[-i-1] for i in range(1, bars))

    def _pullback_to_ma_long(self) -> bool:
        """Check for bullish pullback near signal MA"""
        threshold = self.hp['pullback_threshold']
        distance_pct = abs(self.low - self.signal_ma) / self.signal_ma

        # Price pulled back to within threshold of MA
        touched_ma = distance_pct <= threshold or self.low <= self.signal_ma <= self.high

        # Bullish candle after pullback
        bullish = self.close > self.open

        # Previous bar was bearish (pullback)
        prev_bearish = self.candles[-2, 2] < self.candles[-2, 1]

        return touched_ma and bullish and prev_bearish

    def _pullback_to_ma_short(self) -> bool:
        """Check for bearish rally near signal MA"""
        threshold = self.hp['pullback_threshold']
        distance_pct = abs(self.high - self.signal_ma) / self.signal_ma

        # Price rallied to within threshold of MA
        touched_ma = distance_pct <= threshold or self.low <= self.signal_ma <= self.high

        # Bearish candle after rally
        bearish = self.close < self.open

        # Previous bar was bullish (rally)
        prev_bullish = self.candles[-2, 2] > self.candles[-2, 1]

        return touched_ma and bearish and prev_bullish

    def should_long(self) -> bool:
        return self._is_uptrend() and self._pullback_to_ma_long()

    def should_short(self) -> bool:
        return self._is_downtrend() and self._pullback_to_ma_short()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = min(self.signal_ma - (self.atr * 0.5), entry - (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry + (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def go_short(self):
        entry = self.price
        stop = max(self.signal_ma + (self.atr * 0.5), entry + (self.atr * self.hp['atr_multiplier_sl']))
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = [
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'])),
            (0.5, entry - (self.atr * self.hp['atr_multiplier_tp'] * 1.5)),
        ]

    def update_position(self):
        # Exit if trend breaks
        if self.is_long and self.close < self.trend_ma:
            self.liquidate()
        elif self.is_short and self.close > self.trend_ma:
            self.liquidate()
