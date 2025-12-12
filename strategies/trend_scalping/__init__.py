"""
Trend Following and Scalping Strategies
---------------------------------------
Strategies for trend following and scalping.

Trend Following:
- TF_001: Trend Continuation
- TF_002: Multi-MA Trend
- TF_003: Supertrend Following
- TF_004: ADX Trend
- TF_005: Parabolic Trend
- TF_006: Linear Regression Trend
- TF_007: Price Action Trend
- TF_008: Ichimoku Trend
- TF_009: Moving Average Ribbon
- TF_010: Directional Movement Trend

Scalping:
- SC_001: Micro Scalp
- SC_002: Range Scalp
- SC_003: Momentum Scalp
- SC_004: EMA Scalp
- SC_005: Level Scalp
- SC_006: VWAP Scalp
- SC_007: Bollinger Scalp
- SC_008: Breakout Scalp
- SC_009: Oscillator Scalp
- SC_010: Volume Scalp
"""

from .tf_001_continuation import TrendContinuation
from .tf_002_multi_ma import MultiMATrend
from .tf_003_supertrend import SupertrendFollowing
from .tf_004_adx import ADXTrend
from .tf_005_parabolic import ParabolicTrend
from .tf_006_linreg import LinearRegressionTrend
from .tf_007_price_action import PriceActionTrend
from .tf_008_ichimoku import IchimokuTrend
from .tf_009_ribbon import MARibbonTrend
from .tf_010_dmi import DMITrend
from .sc_001_micro import MicroScalp
from .sc_002_range import RangeScalp
from .sc_003_momentum import MomentumScalp
from .sc_004_ema import EMAScalp
from .sc_005_level import LevelScalp
from .sc_006_vwap import VWAPScalp
from .sc_007_bollinger import BollingerScalp
from .sc_008_breakout import BreakoutScalp
from .sc_009_oscillator import OscillatorScalp
from .sc_010_volume import VolumeScalp

__all__ = [
    'TrendContinuation',
    'MultiMATrend',
    'SupertrendFollowing',
    'ADXTrend',
    'ParabolicTrend',
    'LinearRegressionTrend',
    'PriceActionTrend',
    'IchimokuTrend',
    'MARibbonTrend',
    'DMITrend',
    'MicroScalp',
    'RangeScalp',
    'MomentumScalp',
    'EMAScalp',
    'LevelScalp',
    'VWAPScalp',
    'BollingerScalp',
    'BreakoutScalp',
    'OscillatorScalp',
    'VolumeScalp',
]
