"""
VOL_007: Volume Climax Strategy
-------------------------------
Detect volume climax (exhaustion) patterns.
Extremely high volume often signals trend exhaustion.

Entry Long: Selling climax (high vol on down move, then reversal)
Entry Short: Buying climax (high vol on up move, then reversal)

Optimal Timeframes: 1h, 4h
Complexity: 5/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolumeClimax(Strategy):
    """Volume Climax Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_007"
        self.strategy_name = "Volume Climax"
        self.complexity = 5
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'volume_period', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'climax_mult', 'type': float, 'min': 2.0, 'max': 4.0, 'default': 2.5},
            {'name': 'reversal_bars', 'type': int, 'min': 1, 'max': 3, 'default': 2},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    @property
    def avg_volume(self) -> float:
        return np.mean(self.candles[-self.hp['volume_period']:, 5])

    def _is_volume_climax(self, bar_idx=-1) -> bool:
        """Check if bar has climax volume"""
        volume = self.candles[bar_idx, 5]
        return volume > self.avg_volume * self.hp['climax_mult']

    def _is_down_bar(self, bar_idx=-1) -> bool:
        """Check if bar closed down"""
        return self.candles[bar_idx, 2] < self.candles[bar_idx, 1]

    def _is_up_bar(self, bar_idx=-1) -> bool:
        """Check if bar closed up"""
        return self.candles[bar_idx, 2] > self.candles[bar_idx, 1]

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def selling_climax(self) -> bool:
        """Detect selling climax followed by reversal"""
        reversal_bars = self.hp['reversal_bars']

        # Look for high volume down bar followed by up bars
        for i in range(reversal_bars + 1, reversal_bars + 4):
            idx = -i
            if self._is_volume_climax(idx) and self._is_down_bar(idx):
                # Check for reversal in subsequent bars
                all_up = True
                for j in range(1, reversal_bars + 1):
                    if not self._is_up_bar(idx + j):
                        all_up = False
                        break
                if all_up:
                    return True
        return False

    @property
    def buying_climax(self) -> bool:
        """Detect buying climax followed by reversal"""
        reversal_bars = self.hp['reversal_bars']

        # Look for high volume up bar followed by down bars
        for i in range(reversal_bars + 1, reversal_bars + 4):
            idx = -i
            if self._is_volume_climax(idx) and self._is_up_bar(idx):
                # Check for reversal in subsequent bars
                all_down = True
                for j in range(1, reversal_bars + 1):
                    if not self._is_down_bar(idx + j):
                        all_down = False
                        break
                if all_down:
                    return True
        return False

    def should_long(self) -> bool:
        return self.selling_climax and self._is_up_bar()

    def should_short(self) -> bool:
        return self.buying_climax and self._is_down_bar()

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
        pass  # Let TP/SL handle exits
