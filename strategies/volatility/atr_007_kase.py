"""
ATR_007: Kase Dev Stops Strategy
--------------------------------
Kase DevStops based on true range standard deviations.
More adaptive stops that account for volatility changes.

Entry: Trend following with Kase stops
Exit: Price hits Kase deviation stop

Optimal Timeframes: 1h, 4h, 1d
Complexity: 5/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class KaseDevStops(Strategy):
    """Kase Dev Stops Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ATR_007"
        self.strategy_name = "Kase Dev Stops"
        self.complexity = 5
        self.crypto_suitability = 7
        self._kase_stop_long = None
        self._kase_stop_short = None

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'dev_mult', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'ma_period', 'type': int, 'min': 15, 'max': 50, 'default': 20},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_kase_stops(self):
        """Calculate Kase Dev Stops"""
        period = self.hp['period']
        mult = self.hp['dev_mult']

        high = self.candles[:, 3]
        low = self.candles[:, 4]
        close = self.candles[:, 2]

        # Calculate True Range
        tr = np.zeros(len(self.candles))
        for i in range(1, len(self.candles)):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )

        # Calculate average true range and standard deviation
        atr = np.mean(tr[-period:])
        tr_std = np.std(tr[-period:])

        # Kase Dev Stop = ATR + (std * multiplier)
        kase_dev = atr + (tr_std * mult)

        # Calculate stop levels from recent high/low
        highest = np.max(high[-period:])
        lowest = np.min(low[-period:])

        stop_long = highest - kase_dev
        stop_short = lowest + kase_dev

        return stop_long, stop_short, kase_dev

    @property
    def kase_stop_long(self) -> float:
        stop_long, _, _ = self._calculate_kase_stops()
        return stop_long

    @property
    def kase_stop_short(self) -> float:
        _, stop_short, _ = self._calculate_kase_stops()
        return stop_short

    @property
    def kase_dev(self) -> float:
        _, _, kase_dev = self._calculate_kase_stops()
        return kase_dev

    @property
    def ma(self) -> float:
        return ta.ema(self.candles, period=self.hp['ma_period'])

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def trend_up(self) -> bool:
        return self.close > self.ma

    @property
    def trend_down(self) -> bool:
        return self.close < self.ma

    def _price_above_stop(self) -> bool:
        return self.close > self.kase_stop_long

    def _price_below_stop(self) -> bool:
        return self.close < self.kase_stop_short

    def should_long(self) -> bool:
        # Price crosses above Kase stop long with uptrend
        prev_close = self.candles[-2, 2]
        prev_stop = self._calculate_prev_stops()[0]
        return prev_close <= prev_stop and self.close > self.kase_stop_long and self.trend_up

    def should_short(self) -> bool:
        # Price crosses below Kase stop short with downtrend
        prev_close = self.candles[-2, 2]
        prev_stop = self._calculate_prev_stops()[1]
        return prev_close >= prev_stop and self.close < self.kase_stop_short and self.trend_down

    def _calculate_prev_stops(self):
        """Calculate previous bar's Kase stops"""
        candles = self.candles[:-1]
        period = self.hp['period']
        mult = self.hp['dev_mult']

        if len(candles) < period:
            return 0, float('inf')

        high = candles[:, 3]
        low = candles[:, 4]
        close = candles[:, 2]

        tr = np.zeros(len(candles))
        for i in range(1, len(candles)):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )

        atr = np.mean(tr[-period:])
        tr_std = np.std(tr[-period:])
        kase_dev = atr + (tr_std * mult)

        highest = np.max(high[-period:])
        lowest = np.min(low[-period:])

        return highest - kase_dev, lowest + kase_dev

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.kase_stop_long
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self._kase_stop_long = stop

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry + (self.atr * self.hp['atr_multiplier_tp'])

    def go_short(self):
        entry = self.price
        stop = self.kase_stop_short
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self._kase_stop_short = stop

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, entry - (self.atr * self.hp['atr_multiplier_tp'])

    def update_position(self):
        # Update trailing Kase stops
        if self.is_long:
            new_stop = self.kase_stop_long
            if self._kase_stop_long and new_stop > self._kase_stop_long:
                self._kase_stop_long = new_stop
                self.stop_loss = self.position.qty, new_stop

            if self.low <= self._kase_stop_long:
                self.liquidate()

        elif self.is_short:
            new_stop = self.kase_stop_short
            if self._kase_stop_short and new_stop < self._kase_stop_short:
                self._kase_stop_short = new_stop
                self.stop_loss = self.position.qty, new_stop

            if self.high >= self._kase_stop_short:
                self.liquidate()

    def on_close_position(self, order):
        self._kase_stop_long = None
        self._kase_stop_short = None
