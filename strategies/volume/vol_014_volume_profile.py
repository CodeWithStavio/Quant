"""
VOL_014: Volume Profile Strategy
--------------------------------
Simplified volume profile analysis.
Identifies high-volume price zones (value areas).

Entry Long: Price bounces off value area low (VAL)
Entry Short: Price rejects from value area high (VAH)

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 8/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VolumeProfile(Strategy):
    """Volume Profile Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "VOL_014"
        self.strategy_name = "Volume Profile"
        self.complexity = 6
        self.crypto_suitability = 8

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 50, 'max': 200, 'default': 100},
            {'name': 'num_bins', 'type': int, 'min': 20, 'max': 50, 'default': 30},
            {'name': 'value_area_pct', 'type': float, 'min': 0.6, 'max': 0.8, 'default': 0.7},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 3.0, 'default': 2.0},
            {'name': 'atr_multiplier_tp', 'type': float, 'min': 2.5, 'max': 5.0, 'default': 3.5},
        ]

    def _calculate_volume_profile(self):
        """Calculate simplified volume profile"""
        lookback = min(self.hp['lookback'], len(self.candles) - 1)
        num_bins = self.hp['num_bins']
        value_area_pct = self.hp['value_area_pct']

        candles = self.candles[-lookback:]

        high = candles[:, 3]
        low = candles[:, 4]
        close = candles[:, 2]
        volume = candles[:, 5]

        # Create price bins
        price_min = np.min(low)
        price_max = np.max(high)
        bin_size = (price_max - price_min) / num_bins

        if bin_size == 0:
            return price_min, price_max, (price_min + price_max) / 2

        # Distribute volume across bins
        volume_by_bin = np.zeros(num_bins)

        for i in range(len(candles)):
            # Find which bin(s) this candle spans
            candle_low = low[i]
            candle_high = high[i]
            candle_vol = volume[i]

            low_bin = int((candle_low - price_min) / bin_size)
            high_bin = int((candle_high - price_min) / bin_size)

            low_bin = max(0, min(low_bin, num_bins - 1))
            high_bin = max(0, min(high_bin, num_bins - 1))

            # Distribute volume across bins
            bins_spanned = high_bin - low_bin + 1
            vol_per_bin = candle_vol / bins_spanned

            for b in range(low_bin, high_bin + 1):
                volume_by_bin[b] += vol_per_bin

        # Find Point of Control (POC) - highest volume bin
        poc_bin = np.argmax(volume_by_bin)
        poc_price = price_min + (poc_bin + 0.5) * bin_size

        # Find Value Area (70% of volume around POC)
        total_volume = np.sum(volume_by_bin)
        target_volume = total_volume * value_area_pct

        # Expand from POC until we capture target volume
        va_low_bin = poc_bin
        va_high_bin = poc_bin
        current_volume = volume_by_bin[poc_bin]

        while current_volume < target_volume:
            # Add bin with higher volume (above or below)
            vol_below = volume_by_bin[va_low_bin - 1] if va_low_bin > 0 else 0
            vol_above = volume_by_bin[va_high_bin + 1] if va_high_bin < num_bins - 1 else 0

            if vol_below >= vol_above and va_low_bin > 0:
                va_low_bin -= 1
                current_volume += vol_below
            elif va_high_bin < num_bins - 1:
                va_high_bin += 1
                current_volume += vol_above
            else:
                break

        val = price_min + va_low_bin * bin_size
        vah = price_min + (va_high_bin + 1) * bin_size

        return val, vah, poc_price

    @property
    def value_area_low(self) -> float:
        val, _, _ = self._calculate_volume_profile()
        return val

    @property
    def value_area_high(self) -> float:
        _, vah, _ = self._calculate_volume_profile()
        return vah

    @property
    def poc(self) -> float:
        _, _, poc = self._calculate_volume_profile()
        return poc

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    @property
    def at_val(self) -> bool:
        """Price near value area low"""
        threshold = self.atr * 0.5
        return abs(self.close - self.value_area_low) < threshold

    @property
    def at_vah(self) -> bool:
        """Price near value area high"""
        threshold = self.atr * 0.5
        return abs(self.close - self.value_area_high) < threshold

    @property
    def bounced_from_val(self) -> bool:
        """Price touched VAL and bounced up"""
        return self.low <= self.value_area_low and self.close > self.value_area_low and self.close > self.open

    @property
    def rejected_from_vah(self) -> bool:
        """Price touched VAH and rejected down"""
        return self.high >= self.value_area_high and self.close < self.value_area_high and self.close < self.open

    def should_long(self) -> bool:
        return self.bounced_from_val

    def should_short(self) -> bool:
        return self.rejected_from_vah

    def should_cancel_entry(self) -> bool:
        return False

    def go_long(self):
        entry = self.price
        stop = self.value_area_low - (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, self.poc  # Target POC

    def go_short(self):
        entry = self.price
        stop = self.value_area_high + (self.atr * 0.5)
        qty = utils.size_to_qty(self.balance * 0.02, entry)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = qty, self.poc  # Target POC

    def update_position(self):
        # Exit at POC
        if self.is_long and self.close >= self.poc:
            self.liquidate()
        elif self.is_short and self.close <= self.poc:
            self.liquidate()
