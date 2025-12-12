"""
CRYPTO_005: Correlation Breakdown Strategy
------------------------------------------
Trade when price deviates from typical patterns.

Entry Long: Oversold with bullish divergence
Entry Short: Overbought with bearish divergence

Optimal Timeframes: 1h, 4h
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class CorrelationBreakdown(Strategy):
    """Correlation Breakdown Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "CRYPTO_005"
        self.strategy_name = "Correlation Breakdown"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 20, 'max': 40, 'default': 30},
            {'name': 'deviation_threshold', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 1.5, 'max': 2.5, 'default': 2.0},
        ]

    def _calculate_price_deviation(self) -> float:
        """Calculate how far price deviates from expected"""
        lookback = self.hp['lookback']
        prices = self.candles[-lookback:, 2]

        # Expected price = linear regression
        x = np.arange(lookback)
        slope = np.polyfit(x, prices, 1)[0]
        expected = prices[0] + slope * (lookback - 1)

        # Standard deviation
        std = np.std(prices)
        if std == 0:
            return 0

        return (self.close - expected) / std

    def _has_bullish_divergence(self) -> bool:
        """Check for bullish RSI divergence"""
        # Price making lower lows but RSI making higher lows
        lookback = 10

        price_low_1 = np.min(self.candles[-lookback:-5, 4])
        price_low_2 = np.min(self.candles[-5:, 4])

        rsi_1 = ta.rsi(self.candles[:-5], period=14)
        rsi_2 = ta.rsi(self.candles, period=14)

        return price_low_2 < price_low_1 and rsi_2 > rsi_1

    def _has_bearish_divergence(self) -> bool:
        """Check for bearish RSI divergence"""
        # Price making higher highs but RSI making lower highs
        lookback = 10

        price_high_1 = np.max(self.candles[-lookback:-5, 3])
        price_high_2 = np.max(self.candles[-5:, 3])

        rsi_1 = ta.rsi(self.candles[:-5], period=14)
        rsi_2 = ta.rsi(self.candles, period=14)

        return price_high_2 > price_high_1 and rsi_2 < rsi_1

    @property
    def deviation(self) -> float:
        return self._calculate_price_deviation()

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Price oversold (negative deviation) with bullish divergence
        oversold = self.deviation < -self.hp['deviation_threshold']
        return oversold and self._has_bullish_divergence()

    def should_short(self) -> bool:
        # Price overbought (positive deviation) with bearish divergence
        overbought = self.deviation > self.hp['deviation_threshold']
        return overbought and self._has_bearish_divergence()

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
        # Exit when deviation normalizes
        if abs(self.deviation) < 0.5:
            self.liquidate()
