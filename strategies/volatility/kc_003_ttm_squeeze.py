"""
KC_003: TTM Squeeze Strategy
----------------------------
John Carter's TTM Squeeze - BB inside KC indicates squeeze.
Breakout direction signals trade.

Entry: When squeeze fires (BB expands beyond KC), trade in direction

Optimal Timeframes: 15m, 1h, 4h
Complexity: 5/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class TTMSqueeze(Strategy):
    """TTM Squeeze Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "KC_003"
        self.strategy_name = "TTM Squeeze"
        self.complexity = 5
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'bb_period', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'bb_std', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'kc_period', 'type': int, 'min': 15, 'max': 25, 'default': 20},
            {'name': 'kc_mult', 'type': float, 'min': 1.0, 'max': 2.0, 'default': 1.5},
            {'name': 'mom_period', 'type': int, 'min': 10, 'max': 20, 'default': 12},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 3.0, 'max': 6.0, 'default': 4.0},
        ]

    def _get_bb(self):
        return ta.bollinger_bands(
            self.candles,
            period=self.hp['bb_period'],
            devup=self.hp['bb_std'],
            devdn=self.hp['bb_std']
        )

    def _get_kc(self):
        ema = ta.ema(self.candles, period=self.hp['kc_period'])
        atr_val = ta.atr(self.candles, period=self.hp['kc_period'])
        upper = ema + (atr_val * self.hp['kc_mult'])
        lower = ema - (atr_val * self.hp['kc_mult'])
        return upper, ema, lower

    def _get_momentum(self) -> float:
        """Calculate momentum histogram (linear regression deviation)"""
        close = self.candles[:, 2]
        high = self.candles[:, 3]
        low = self.candles[:, 4]
        period = self.hp['mom_period']

        # Simple momentum approximation
        mid = (high[-period:].max() + low[-period:].min()) / 2
        return close[-1] - mid

    @property
    def in_squeeze(self) -> bool:
        """BB is inside KC (squeeze on)"""
        bb_upper, bb_middle, bb_lower = self._get_bb()
        kc_upper, kc_middle, kc_lower = self._get_kc()
        return bb_lower > kc_lower and bb_upper < kc_upper

    @property
    def in_squeeze_prev(self) -> bool:
        """Was in squeeze previous bar"""
        bb_upper, bb_middle, bb_lower = ta.bollinger_bands(
            self.candles[:-1],
            period=self.hp['bb_period'],
            devup=self.hp['bb_std'],
            devdn=self.hp['bb_std']
        )
        ema = ta.ema(self.candles[:-1], period=self.hp['kc_period'])
        atr_val = ta.atr(self.candles[:-1], period=self.hp['kc_period'])
        kc_upper = ema + (atr_val * self.hp['kc_mult'])
        kc_lower = ema - (atr_val * self.hp['kc_mult'])
        return bb_lower > kc_lower and bb_upper < kc_upper

    @property
    def momentum(self) -> float:
        return self._get_momentum()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def _squeeze_fired_long(self) -> bool:
        """Squeeze fired with bullish momentum"""
        return self.in_squeeze_prev and not self.in_squeeze and self.momentum > 0

    def _squeeze_fired_short(self) -> bool:
        """Squeeze fired with bearish momentum"""
        return self.in_squeeze_prev and not self.in_squeeze and self.momentum < 0

    def should_long(self) -> bool:
        return self._squeeze_fired_long()

    def should_short(self) -> bool:
        return self._squeeze_fired_short()

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
        # Exit when momentum reverses
        if self.is_long and self.momentum < 0:
            self.liquidate()
        elif self.is_short and self.momentum > 0:
            self.liquidate()
