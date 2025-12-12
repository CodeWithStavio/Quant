"""
MTF_010: Timeframe Price Action Strategy
----------------------------------------
Price action patterns confirmed across timeframe views.

Entry Long: HTF higher lows with LTF bullish pattern
Entry Short: HTF lower highs with LTF bearish pattern

Optimal Timeframes: 15m, 1h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TFPriceAction(Strategy):
    """Timeframe Price Action Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MTF_010"
        self.strategy_name = "TF Price Action"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'htf_lookback', 'type': int, 'min': 80, 'max': 150, 'default': 100},
            {'name': 'ltf_lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _find_htf_swing_lows(self) -> List[float]:
        """Find swing lows in HTF view"""
        lookback = self.hp['htf_lookback']
        lows = self.candles[-lookback:, 4]
        swing_lows = []
        for i in range(5, len(lows) - 5):
            if lows[i] < min(lows[i-5:i]) and lows[i] < min(lows[i+1:i+6]):
                swing_lows.append(lows[i])
        return swing_lows

    def _find_htf_swing_highs(self) -> List[float]:
        """Find swing highs in HTF view"""
        lookback = self.hp['htf_lookback']
        highs = self.candles[-lookback:, 3]
        swing_highs = []
        for i in range(5, len(highs) - 5):
            if highs[i] > max(highs[i-5:i]) and highs[i] > max(highs[i+1:i+6]):
                swing_highs.append(highs[i])
        return swing_highs

    @property
    def htf_higher_lows(self) -> bool:
        lows = self._find_htf_swing_lows()
        if len(lows) < 2:
            return False
        return lows[-1] > lows[-2]

    @property
    def htf_lower_highs(self) -> bool:
        highs = self._find_htf_swing_highs()
        if len(highs) < 2:
            return False
        return highs[-1] < highs[-2]

    @property
    def ltf_bullish_engulf(self) -> bool:
        """Simple bullish engulfing on LTF"""
        prev_open = self.candles[-2, 1]
        prev_close = self.candles[-2, 2]
        if prev_close >= prev_open:
            return False
        return self.close > self.open and self.close > prev_open and self.open < prev_close

    @property
    def ltf_bearish_engulf(self) -> bool:
        """Simple bearish engulfing on LTF"""
        prev_open = self.candles[-2, 1]
        prev_close = self.candles[-2, 2]
        if prev_close <= prev_open:
            return False
        return self.close < self.open and self.close < prev_open and self.open > prev_close

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self.htf_higher_lows and self.ltf_bullish_engulf

    def should_short(self) -> bool:
        return self.htf_lower_highs and self.ltf_bearish_engulf

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
        pass
