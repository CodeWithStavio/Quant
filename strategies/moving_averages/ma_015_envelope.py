"""
MA_015: Moving Average Envelope Strategy
----------------------------------------
Uses bands at fixed percentage above/below MA for mean reversion.

Upper Envelope = MA * (1 + percentage)
Lower Envelope = MA * (1 - percentage)

Entry Long: Price touches/crosses below lower envelope
Entry Short: Price touches/crosses above upper envelope

Optimal Timeframes: 15m, 1h, 4h
Complexity: 2/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class MAEnvelope(Strategy):
    """Moving Average Envelope Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "MA_015"
        self.strategy_name = "MA Envelope"
        self.complexity = 2
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'ma_period', 'type': int, 'min': 10, 'max': 50, 'default': 20},
            {'name': 'envelope_pct', 'type': float, 'min': 0.01, 'max': 0.05, 'default': 0.02},
            {'name': 'ma_type', 'type': str, 'default': 'sma'},
            {'name': 'require_reversal', 'type': bool, 'default': True},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.5},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 2.0},
        ]

    @property
    def ma(self) -> float:
        if self.hp.get('ma_type', 'sma') == 'ema':
            return ta.ema(self.candles, period=self.hp['ma_period'])
        return ta.sma(self.candles, period=self.hp['ma_period'])

    @property
    def upper_envelope(self) -> float:
        return self.ma * (1 + self.hp['envelope_pct'])

    @property
    def lower_envelope(self) -> float:
        return self.ma * (1 - self.hp['envelope_pct'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _at_lower_envelope(self) -> bool:
        """Check if price at or below lower envelope"""
        return self.low <= self.lower_envelope

    def _at_upper_envelope(self) -> bool:
        """Check if price at or above upper envelope"""
        return self.high >= self.upper_envelope

    def _bullish_reversal(self) -> bool:
        """Check for bullish reversal candle"""
        if not self.hp.get('require_reversal', True):
            return True

        # Current candle is bullish
        bullish = self.close > self.open

        # Lower wick shows rejection
        body = abs(self.close - self.open)
        lower_wick = min(self.open, self.close) - self.low
        has_rejection = lower_wick > body * 0.5

        return bullish and has_rejection

    def _bearish_reversal(self) -> bool:
        """Check for bearish reversal candle"""
        if not self.hp.get('require_reversal', True):
            return True

        # Current candle is bearish
        bearish = self.close < self.open

        # Upper wick shows rejection
        body = abs(self.close - self.open)
        upper_wick = self.high - max(self.open, self.close)
        has_rejection = upper_wick > body * 0.5

        return bearish and has_rejection

    def should_long(self) -> bool:
        return self._at_lower_envelope() and self._bullish_reversal()

    def should_short(self) -> bool:
        return self._at_upper_envelope() and self._bearish_reversal()

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.lower_envelope - (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        # Target the MA (middle) and upper envelope
        self.take_profit = [
            (0.6, self.ma),
            (0.4, self.upper_envelope),
        ]

    def go_short(self):
        entry = self.price
        stop = self.upper_envelope + (self.atr * self.hp['atr_multiplier_sl'])
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        # Target the MA (middle) and lower envelope
        self.take_profit = [
            (0.6, self.ma),
            (0.4, self.lower_envelope),
        ]

    def update_position(self):
        # Optionally exit at MA
        if self.is_long and self.close >= self.ma:
            # Keep partial, let rest run to upper envelope
            pass
        elif self.is_short and self.close <= self.ma:
            pass
