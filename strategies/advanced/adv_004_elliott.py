"""
ADV_004: Elliott Wave Proxy Strategy
------------------------------------
Simplified Elliott wave pattern detection.

Entry Long: Wave 3 or 5 opportunity
Entry Short: Corrective wave C opportunity

Optimal Timeframes: 4h, 1d
Complexity: 8/10
Crypto Suitability: 7/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class ElliottWaveProxy(Strategy):
    """Elliott Wave Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ADV_004"
        self.strategy_name = "Elliott Wave Proxy"
        self.complexity = 8
        self.crypto_suitability = 7

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 30, 'max': 80, 'default': 50},
            {'name': 'fib_tolerance', 'type': float, 'min': 0.05, 'max': 0.15, 'default': 0.1},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _find_waves(self) -> list:
        """Find swing points that could form waves"""
        lookback = self.hp['lookback']
        swings = []

        for i in range(5, lookback):
            if i + 3 >= len(self.candles):
                continue

            # Swing high
            if (self.candles[-i, 3] > self.candles[-i-1, 3] and
                self.candles[-i, 3] > self.candles[-i+1, 3]):
                swings.append({'type': 'high', 'price': self.candles[-i, 3], 'idx': -i})

            # Swing low
            if (self.candles[-i, 4] < self.candles[-i-1, 4] and
                self.candles[-i, 4] < self.candles[-i+1, 4]):
                swings.append({'type': 'low', 'price': self.candles[-i, 4], 'idx': -i})

        return sorted(swings, key=lambda x: x['idx'], reverse=True)[:8]

    def _is_wave_3_setup(self) -> bool:
        """Detect potential wave 3 setup (strongest impulse)"""
        swings = self._find_waves()
        if len(swings) < 4:
            return False

        # Looking for: wave 1 up, wave 2 correction (38.2-61.8%), wave 3 starting
        highs = [s for s in swings if s['type'] == 'high']
        lows = [s for s in swings if s['type'] == 'low']

        if len(highs) < 1 or len(lows) < 2:
            return False

        wave1_low = lows[-1]['price'] if lows else self.close
        wave1_high = highs[-1]['price'] if highs else self.close
        wave2_low = lows[0]['price'] if len(lows) > 1 else wave1_low

        wave1_range = wave1_high - wave1_low
        if wave1_range <= 0:
            return False

        retracement = (wave1_high - wave2_low) / wave1_range

        # Wave 2 typically retraces 38.2% to 61.8%
        valid_retracement = 0.382 - self.hp['fib_tolerance'] < retracement < 0.618 + self.hp['fib_tolerance']

        # Price bouncing from wave 2 low
        near_wave2_low = self.close < wave2_low * 1.02

        return valid_retracement and near_wave2_low and self.close > self.open

    def _is_wave_c_setup(self) -> bool:
        """Detect potential wave C setup (corrective wave)"""
        swings = self._find_waves()
        if len(swings) < 4:
            return False

        highs = [s for s in swings if s['type'] == 'high']
        lows = [s for s in swings if s['type'] == 'low']

        if len(highs) < 2 or len(lows) < 1:
            return False

        # Looking for ABC correction pattern
        wave_a_high = highs[-1]['price']
        wave_b_low = lows[0]['price']
        current_high = self.high

        # Wave B typically retraces 50-61.8% of wave A
        wave_a_range = wave_a_high - wave_b_low
        if wave_a_range <= 0:
            return False

        # Near potential wave C high
        near_resistance = self.high > wave_a_high * 0.95

        return near_resistance and self.close < self.open

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        return self._is_wave_3_setup()

    def should_short(self) -> bool:
        return self._is_wave_c_setup()

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
        # Trail with ATR
        if self.is_long:
            trail = self.close - (self.atr * 1.5)
            if trail > self.average_entry_price:
                self.stop_loss = self.position.qty, trail
        elif self.is_short:
            trail = self.close + (self.atr * 1.5)
            if trail < self.average_entry_price:
                self.stop_loss = self.position.qty, trail
