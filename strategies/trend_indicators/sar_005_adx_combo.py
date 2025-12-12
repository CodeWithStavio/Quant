"""
SAR_005: SAR + ADX Combo Strategy
---------------------------------
Combine SAR signals with ADX trend strength.
Only trade SAR signals when ADX confirms trend.

Entry Long: SAR bullish + ADX > threshold + +DI > -DI
Entry Short: SAR bearish + ADX > threshold + -DI > +DI

Optimal Timeframes: 1h, 4h
Complexity: 4/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class SARADXCombo(Strategy):
    """SAR + ADX Combo Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "SAR_005"
        self.strategy_name = "SAR + ADX Combo"
        self.complexity = 4
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'sar_acceleration', 'type': float, 'min': 0.01, 'max': 0.03, 'default': 0.02},
            {'name': 'sar_maximum', 'type': float, 'min': 0.15, 'max': 0.25, 'default': 0.2},
            {'name': 'adx_period', 'type': int, 'min': 10, 'max': 21, 'default': 14},
            {'name': 'adx_threshold', 'type': float, 'min': 20, 'max': 30, 'default': 25},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_sar(self):
        high = self.candles[:, 3]
        low = self.candles[:, 4]
        af = self.hp['sar_acceleration']
        max_af = self.hp['sar_maximum']

        sar = np.zeros(len(self.candles))
        trend = np.zeros(len(self.candles))
        ep = np.zeros(len(self.candles))
        af_vals = np.zeros(len(self.candles))

        sar[0] = low[0]
        trend[0] = 1
        ep[0] = high[0]
        af_vals[0] = af

        for i in range(1, len(self.candles)):
            if trend[i-1] == 1:
                sar[i] = sar[i-1] + af_vals[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = min(sar[i], low[i-1], low[max(0, i-2)] if i > 1 else low[i-1])

                if low[i] < sar[i]:
                    trend[i] = -1
                    sar[i] = ep[i-1]
                    ep[i] = low[i]
                    af_vals[i] = af
                else:
                    trend[i] = 1
                    ep[i] = max(ep[i-1], high[i])
                    af_vals[i] = min(af_vals[i-1] + af, max_af) if high[i] > ep[i-1] else af_vals[i-1]
            else:
                sar[i] = sar[i-1] + af_vals[i-1] * (ep[i-1] - sar[i-1])
                sar[i] = max(sar[i], high[i-1], high[max(0, i-2)] if i > 1 else high[i-1])

                if high[i] > sar[i]:
                    trend[i] = 1
                    sar[i] = ep[i-1]
                    ep[i] = high[i]
                    af_vals[i] = af
                else:
                    trend[i] = -1
                    ep[i] = min(ep[i-1], low[i])
                    af_vals[i] = min(af_vals[i-1] + af, max_af) if low[i] < ep[i-1] else af_vals[i-1]

        return sar, trend

    def _calculate_adx(self):
        period = self.hp['adx_period']
        high = self.candles[:, 3]
        low = self.candles[:, 4]
        close = self.candles[:, 2]

        tr = np.zeros(len(self.candles))
        plus_dm = np.zeros(len(self.candles))
        minus_dm = np.zeros(len(self.candles))

        for i in range(1, len(self.candles)):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move

        atr = np.zeros(len(self.candles))
        plus_di_raw = np.zeros(len(self.candles))
        minus_di_raw = np.zeros(len(self.candles))

        atr[period] = np.sum(tr[1:period+1])
        plus_di_raw[period] = np.sum(plus_dm[1:period+1])
        minus_di_raw[period] = np.sum(minus_dm[1:period+1])

        for i in range(period + 1, len(self.candles)):
            atr[i] = atr[i-1] - (atr[i-1] / period) + tr[i]
            plus_di_raw[i] = plus_di_raw[i-1] - (plus_di_raw[i-1] / period) + plus_dm[i]
            minus_di_raw[i] = minus_di_raw[i-1] - (minus_di_raw[i-1] / period) + minus_dm[i]

        atr = np.where(atr == 0, 1, atr)
        plus_di = 100 * plus_di_raw / atr
        minus_di = 100 * minus_di_raw / atr

        di_sum = plus_di + minus_di
        di_sum = np.where(di_sum == 0, 1, di_sum)
        dx = 100 * np.abs(plus_di - minus_di) / di_sum

        adx = np.zeros(len(self.candles))
        if len(self.candles) > period * 2:
            adx[period * 2] = np.mean(dx[period:period * 2 + 1])
            for i in range(period * 2 + 1, len(self.candles)):
                adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period

        return adx[-1], plus_di[-1], minus_di[-1]

    @property
    def sar(self) -> float:
        sar, _ = self._calculate_sar()
        return sar[-1]

    @property
    def sar_trend(self) -> int:
        _, trend = self._calculate_sar()
        return int(trend[-1])

    @property
    def sar_trend_prev(self) -> int:
        _, trend = self._calculate_sar()
        return int(trend[-2]) if len(trend) > 1 else int(trend[-1])

    @property
    def adx(self) -> float:
        adx, _, _ = self._calculate_adx()
        return adx

    @property
    def plus_di(self) -> float:
        _, plus_di, _ = self._calculate_adx()
        return plus_di

    @property
    def minus_di(self) -> float:
        _, _, minus_di = self._calculate_adx()
        return minus_di

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def sar_bullish_flip(self) -> bool:
        return self.sar_trend_prev == -1 and self.sar_trend == 1

    @property
    def sar_bearish_flip(self) -> bool:
        return self.sar_trend_prev == 1 and self.sar_trend == -1

    @property
    def strong_trend(self) -> bool:
        return self.adx > self.hp['adx_threshold']

    @property
    def bullish_di(self) -> bool:
        return self.plus_di > self.minus_di

    @property
    def bearish_di(self) -> bool:
        return self.minus_di > self.plus_di

    def should_long(self) -> bool:
        return self.sar_bullish_flip and self.strong_trend and self.bullish_di

    def should_short(self) -> bool:
        return self.sar_bearish_flip and self.strong_trend and self.bearish_di

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
        if self.is_long and self.sar_trend == -1:
            self.liquidate()
        elif self.is_short and self.sar_trend == 1:
            self.liquidate()
