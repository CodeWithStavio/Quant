"""
ONCHAIN_006: Velocity Proxy Strategy
------------------------------------
Measure token velocity using volume/price ratios.

Entry Long: Low velocity with rising price (accumulation)
Entry Short: High velocity with falling price (distribution)

Optimal Timeframes: 4h, 1d
Complexity: 6/10
Crypto Suitability: 9/10
"""

from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import List, Dict


class VelocityProxy(Strategy):
    """Velocity Proxy Strategy"""

    def __init__(self):
        super().__init__()
        self.strategy_id = "ONCHAIN_006"
        self.strategy_name = "Velocity Proxy"
        self.complexity = 6
        self.crypto_suitability = 9

    @property
    def hyperparameters(self) -> List[Dict]:
        return [
            {'name': 'lookback', 'type': int, 'min': 15, 'max': 30, 'default': 20},
            {'name': 'low_velocity_pct', 'type': float, 'min': 20, 'max': 35, 'default': 25},
            {'name': 'high_velocity_pct', 'type': float, 'min': 65, 'max': 80, 'default': 75},
            {'name': 'atr_multiplier_sl', 'type': float, 'min': 2.0, 'max': 3.0, 'default': 2.5},
        ]

    def _calculate_velocity(self) -> float:
        """Calculate velocity proxy: turnover rate"""
        lookback = self.hp['lookback']
        # Velocity = Volume / Market Cap proxy
        total_volume = np.sum(self.candles[-lookback:, 5])
        avg_price = np.mean(self.candles[-lookback:, 2])
        return total_volume / (avg_price * lookback) if avg_price > 0 else 1

    def _get_velocity_percentile(self) -> float:
        """Get current velocity percentile"""
        lookback = self.hp['lookback']
        current_velocity = self._calculate_velocity()

        velocity_history = []
        for i in range(1, lookback * 2):
            if len(self.candles) > lookback + i:
                vol = np.sum(self.candles[-lookback-i:-i, 5])
                price = np.mean(self.candles[-lookback-i:-i, 2])
                if price > 0:
                    velocity_history.append(vol / (price * lookback))

        if not velocity_history:
            return 50

        return np.sum(np.array(velocity_history) < current_velocity) / len(velocity_history) * 100

    @property
    def velocity_percentile(self) -> float:
        return self._get_velocity_percentile()

    @property
    def price_trend(self) -> float:
        """Simple price trend direction"""
        lookback = self.hp['lookback']
        first_half = np.mean(self.candles[-lookback:-lookback//2, 2])
        second_half = np.mean(self.candles[-lookback//2:, 2])
        return (second_half - first_half) / first_half * 100

    @property
    def atr(self) -> float:
        return ta.atr(self.candles, period=14)

    def should_long(self) -> bool:
        # Low velocity + rising price = accumulation
        low_vel = self.velocity_percentile < self.hp['low_velocity_pct']
        rising = self.price_trend > 1
        return low_vel and rising

    def should_short(self) -> bool:
        # High velocity + falling price = distribution
        high_vel = self.velocity_percentile > self.hp['high_velocity_pct']
        falling = self.price_trend < -1
        return high_vel and falling

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
        # Exit on velocity normalization
        if self.is_long and self.velocity_percentile > 50:
            self.liquidate()
        elif self.is_short and self.velocity_percentile < 50:
            self.liquidate()
