"""
Volatility-Based Strategies
---------------------------
Keltner Channels, Donchian Channels, and ATR-based strategies.

Keltner Channels:
- KC_001: Keltner Channel Breakout
- KC_002: Keltner Channel Mean Reversion
- KC_003: TTM Squeeze
- KC_004: Keltner + MACD Confirmation

Donchian Channels:
- DC_001: Donchian Channel Breakout (Turtle)
- DC_002: Donchian Mid-Line Strategy
- DC_003: Dual Donchian (System 1 & 2)
- DC_004: Donchian Width Volatility

ATR-Based:
- ATR_001: ATR Breakout
- ATR_002: SuperTrend
- ATR_003: ATR Trailing Stop
- ATR_004: Chandelier Exit
- ATR_005: Volatility Ratio
- ATR_006: ATR Channel
- ATR_007: Kase Dev Stops
"""

from .kc_001_breakout import KeltnerBreakout
from .kc_002_mean_reversion import KeltnerMeanReversion
from .kc_003_ttm_squeeze import TTMSqueeze
from .kc_004_macd import KeltnerMACD
from .dc_001_turtle import DonchianTurtle
from .dc_002_midline import DonchianMidline
from .dc_003_dual import DualDonchian
from .dc_004_width import DonchianWidth
from .atr_001_breakout import ATRBreakout
from .atr_002_supertrend import SuperTrendStrategy
from .atr_003_trailing import ATRTrailingStop
from .atr_004_chandelier import ChandelierExit
from .atr_005_volatility_ratio import VolatilityRatio
from .atr_006_channel import ATRChannel
from .atr_007_kase import KaseDevStops

__all__ = [
    'KeltnerBreakout',
    'KeltnerMeanReversion',
    'TTMSqueeze',
    'KeltnerMACD',
    'DonchianTurtle',
    'DonchianMidline',
    'DualDonchian',
    'DonchianWidth',
    'ATRBreakout',
    'SuperTrendStrategy',
    'ATRTrailingStop',
    'ChandelierExit',
    'VolatilityRatio',
    'ATRChannel',
    'KaseDevStops',
]
