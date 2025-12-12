"""
Base Strategy Class
-------------------
Foundation class for all Jesse trading strategies with common functionality.
"""

from abc import ABC, abstractmethod
from jesse.strategies import Strategy
from jesse import utils
import jesse.indicators as ta
import numpy as np
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime

import sys
sys.path.append('..')
from utils.signal_output import SignalOutput, SignalType, TradingSignal
from utils.helpers import (
    crossover, crossunder, atr_stop_loss, atr_take_profit,
    calculate_risk_reward, detect_divergence, z_score
)


class BaseStrategy(Strategy):
    """
    Base strategy class with common functionality for all Jesse strategies.

    Provides:
    - Signal output system
    - Risk management utilities
    - Common indicator access
    - Position sizing
    - Logging and debugging
    """

    def __init__(self):
        super().__init__()

        # Strategy metadata
        self.strategy_id: str = "BASE_000"
        self.strategy_name: str = "Base Strategy"
        self.strategy_category: str = "base"
        self.complexity_rating: int = 1  # 1-10 scale
        self.crypto_suitability: int = 5  # 1-10 scale

        # Risk management defaults
        self.risk_per_trade: float = 0.02  # 2%
        self.max_position_pct: float = 0.10  # 10% max
        self.default_sl_atr_mult: float = 2.0
        self.default_tp_atr_mult: float = 3.0

        # Signal output
        self.signal_output = SignalOutput(
            output_dir="signals",
            console_output=True,
            file_output=True
        )

        # Internal state
        self._last_signal_bar: int = 0
        self._trade_count: int = 0

    # ==================== HYPERPARAMETERS ====================

    @property
    def hyperparameters(self) -> List[Dict]:
        """
        Override in subclass to define strategy parameters.
        Used for optimization and backtesting.
        """
        return []

    # ==================== CORE METHODS (OVERRIDE IN SUBCLASS) ====================

    @abstractmethod
    def should_long(self) -> bool:
        """Return True if long entry conditions are met"""
        pass

    @abstractmethod
    def should_short(self) -> bool:
        """Return True if short entry conditions are met"""
        pass

    def should_cancel_entry(self) -> bool:
        """Return True if pending entry should be cancelled"""
        return False

    def filters(self) -> List[List]:
        """
        Define filter conditions that must pass before entry.
        Override in subclass to add filters.

        Returns:
            List of [condition, description] pairs
        """
        return []

    # ==================== POSITION MANAGEMENT ====================

    def go_long(self):
        """Execute long entry with risk management"""
        entry = self.price
        stop = self._calculate_stop_loss(is_long=True)
        qty = self._calculate_position_size(entry, stop)

        self.buy = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = self._calculate_take_profits(entry, stop, is_long=True)

        self._emit_signal(SignalType.LONG, entry, stop)

    def go_short(self):
        """Execute short entry with risk management"""
        entry = self.price
        stop = self._calculate_stop_loss(is_long=False)
        qty = self._calculate_position_size(entry, stop)

        self.sell = qty, entry
        self.stop_loss = qty, stop
        self.take_profit = self._calculate_take_profits(entry, stop, is_long=False)

        self._emit_signal(SignalType.SHORT, entry, stop)

    def update_position(self):
        """
        Called on every candle while position is open.
        Override in subclass for trailing stops, partial exits, etc.
        """
        pass

    # ==================== RISK MANAGEMENT HELPERS ====================

    def _calculate_stop_loss(self, is_long: bool) -> float:
        """Calculate stop loss based on ATR"""
        atr = self.atr(14)
        return atr_stop_loss(
            self.price, atr,
            multiplier=self.default_sl_atr_mult,
            is_long=is_long
        )

    def _calculate_take_profits(
        self,
        entry: float,
        stop: float,
        is_long: bool
    ) -> List[Tuple[float, float]]:
        """
        Calculate multiple take profit levels.

        Returns list of (quantity_pct, price) tuples for Jesse's take_profit
        """
        risk = abs(entry - stop)

        if is_long:
            tp1 = entry + (risk * 1.5)  # 1.5R
            tp2 = entry + (risk * 2.5)  # 2.5R
            tp3 = entry + (risk * 4.0)  # 4R
        else:
            tp1 = entry - (risk * 1.5)
            tp2 = entry - (risk * 2.5)
            tp3 = entry - (risk * 4.0)

        # Return with quantity distribution
        return [
            (0.4, tp1),   # 40% at TP1
            (0.3, tp2),   # 30% at TP2
            (0.3, tp3),   # 30% at TP3
        ]

    def _calculate_position_size(self, entry: float, stop: float) -> float:
        """Calculate position size based on risk"""
        risk_amount = self.balance * self.risk_per_trade
        risk_per_unit = abs(entry - stop)

        if risk_per_unit == 0:
            return 0

        # Calculate raw quantity
        qty = risk_amount / risk_per_unit

        # Apply max position limit
        max_qty = (self.balance * self.max_position_pct) / entry
        qty = min(qty, max_qty)

        # Use Jesse's utility for proper sizing
        return utils.size_to_qty(qty * entry, entry)

    # ==================== SIGNAL OUTPUT ====================

    def _emit_signal(
        self,
        signal_type: SignalType,
        entry: float,
        stop: float,
        confidence: float = 0.5
    ):
        """Emit trading signal through signal output system"""
        take_profits = self._calculate_take_profits(entry, stop, signal_type == SignalType.LONG)

        signal = self.signal_output.create_signal(
            symbol=self.symbol,
            timeframe=self.timeframe,
            strategy_id=self.strategy_id,
            strategy_name=self.strategy_name,
            signal_type=signal_type,
            entry_price=entry,
            confidence=confidence,
            stop_loss=stop,
            take_profit_1=take_profits[0][1] if take_profits else None,
            take_profit_2=take_profits[1][1] if len(take_profits) > 1 else None,
            take_profit_3=take_profits[2][1] if len(take_profits) > 2 else None,
            indicators_state=self._get_indicators_state(),
        )

        self.signal_output.emit(signal)
        self._last_signal_bar = self.index
        self._trade_count += 1

    def _get_indicators_state(self) -> Dict[str, Any]:
        """
        Override in subclass to provide current indicator values.
        """
        return {}

    # ==================== COMMON INDICATORS ====================

    def sma(self, period: int, source: str = 'close') -> float:
        """Simple Moving Average"""
        return ta.sma(self.candles, period=period, source_type=source)

    def ema(self, period: int, source: str = 'close') -> float:
        """Exponential Moving Average"""
        return ta.ema(self.candles, period=period, source_type=source)

    def rsi(self, period: int = 14, source: str = 'close') -> float:
        """Relative Strength Index"""
        return ta.rsi(self.candles, period=period, source_type=source)

    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9):
        """MACD - Returns (macd, signal, histogram)"""
        return ta.macd(self.candles, fast_period=fast, slow_period=slow, signal_period=signal)

    def bollinger_bands(self, period: int = 20, std_dev: float = 2.0):
        """Bollinger Bands - Returns (upper, middle, lower)"""
        return ta.bollinger_bands(self.candles, period=period, devup=std_dev, devdn=std_dev)

    def atr(self, period: int = 14) -> float:
        """Average True Range"""
        return ta.atr(self.candles, period=period)

    def stochastic(self, k: int = 14, d: int = 3, smooth: int = 3):
        """Stochastic Oscillator - Returns (k, d)"""
        return ta.stoch(self.candles, fastk_period=k, slowk_period=smooth, slowd_period=d)

    def adx(self, period: int = 14) -> float:
        """Average Directional Index"""
        return ta.adx(self.candles, period=period)

    def supertrend(self, period: int = 10, multiplier: float = 3.0):
        """SuperTrend indicator - Returns (trend, direction)"""
        return ta.supertrend(self.candles, period=period, factor=multiplier)

    def ichimoku(self):
        """Ichimoku Cloud - Returns tuple of components"""
        return ta.ichimoku_cloud(self.candles)

    def vwap(self) -> float:
        """Volume Weighted Average Price"""
        return ta.vwap(self.candles)

    def cci(self, period: int = 20) -> float:
        """Commodity Channel Index"""
        return ta.cci(self.candles, period=period)

    def williams_r(self, period: int = 14) -> float:
        """Williams %R"""
        return ta.willr(self.candles, period=period)

    def obv(self) -> float:
        """On Balance Volume"""
        return ta.obv(self.candles)

    def mfi(self, period: int = 14) -> float:
        """Money Flow Index"""
        return ta.mfi(self.candles, period=period)

    def psar(self):
        """Parabolic SAR"""
        return ta.psar(self.candles)

    def donchian(self, period: int = 20):
        """Donchian Channels - Returns (upper, middle, lower)"""
        return ta.donchian(self.candles, period=period)

    def keltner(self, period: int = 20, multiplier: float = 2.0):
        """Keltner Channels"""
        return ta.keltner(self.candles, period=period, multiplier=multiplier)

    # ==================== UTILITY METHODS ====================

    def is_new_bar(self) -> bool:
        """Check if this is a new bar (prevents multiple signals per bar)"""
        return self._last_signal_bar != self.index

    def trend_direction(self, ma_period: int = 50) -> int:
        """
        Determine trend direction.
        Returns: 1 for uptrend, -1 for downtrend, 0 for sideways
        """
        ma = self.ema(ma_period)

        if self.close > ma * 1.01:
            return 1
        elif self.close < ma * 0.99:
            return -1
        return 0

    def volatility_state(self, lookback: int = 20) -> str:
        """
        Assess current volatility state.
        Returns: 'high', 'normal', or 'low'
        """
        current_atr = self.atr(14)
        avg_atr = np.mean([self.atr(14)] * lookback)  # Simplified

        ratio = current_atr / avg_atr if avg_atr > 0 else 1

        if ratio > 1.5:
            return 'high'
        elif ratio < 0.7:
            return 'low'
        return 'normal'

    def market_regime(self) -> str:
        """
        Detect market regime.
        Returns: 'trending_up', 'trending_down', 'ranging'
        """
        adx_val = self.adx(14)
        trend = self.trend_direction()

        if adx_val > 25:
            if trend > 0:
                return 'trending_up'
            elif trend < 0:
                return 'trending_down'
        return 'ranging'

    # ==================== LOGGING ====================

    def log(self, message: str):
        """Log message with strategy context"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.strategy_id}] {message}")

    def debug(self, message: str):
        """Debug logging (can be disabled)"""
        if getattr(self, 'debug_mode', False):
            self.log(f"DEBUG: {message}")
