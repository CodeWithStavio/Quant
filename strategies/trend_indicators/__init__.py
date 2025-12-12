"""
Trend Indicator Strategies
--------------------------
Ichimoku Cloud, ADX, and Parabolic SAR based strategies.

Ichimoku Cloud:
- ICH_001: Ichimoku Cloud Crossover
- ICH_002: Ichimoku TK Cross
- ICH_003: Ichimoku Kumo Breakout
- ICH_004: Ichimoku Chikou Span
- ICH_005: Ichimoku Multi-Signal
- ICH_006: Ichimoku Kijun Bounce

ADX (Average Directional Index):
- ADX_001: ADX Trend Strength
- ADX_002: ADX DI Crossover
- ADX_003: ADX Breakout
- ADX_004: ADX Trend Filter
- ADX_005: ADX Extreme

Parabolic SAR:
- SAR_001: Parabolic SAR Basic
- SAR_002: SAR + MA Filter
- SAR_003: SAR Reversal
- SAR_004: SAR Trailing Stop
- SAR_005: SAR + ADX Combo
- SAR_006: Multi-Timeframe SAR
"""

from .ich_001_cloud_crossover import IchimokuCloudCrossover
from .ich_002_tk_cross import IchimokuTKCross
from .ich_003_kumo_breakout import IchimokuKumoBreakout
from .ich_004_chikou_span import IchimokuChikouSpan
from .ich_005_multi_signal import IchimokuMultiSignal
from .ich_006_kijun_bounce import IchimokuKijunBounce
from .adx_001_trend_strength import ADXTrendStrength
from .adx_002_di_crossover import ADXDICrossover
from .adx_003_breakout import ADXBreakout
from .adx_004_trend_filter import ADXTrendFilter
from .adx_005_extreme import ADXExtreme
from .sar_001_basic import SARBasic
from .sar_002_ma_filter import SARMAFilter
from .sar_003_reversal import SARReversal
from .sar_004_trailing import SARTrailing
from .sar_005_adx_combo import SARADXCombo
from .sar_006_mtf import SARMultiTimeframe

__all__ = [
    'IchimokuCloudCrossover',
    'IchimokuTKCross',
    'IchimokuKumoBreakout',
    'IchimokuChikouSpan',
    'IchimokuMultiSignal',
    'IchimokuKijunBounce',
    'ADXTrendStrength',
    'ADXDICrossover',
    'ADXBreakout',
    'ADXTrendFilter',
    'ADXExtreme',
    'SARBasic',
    'SARMAFilter',
    'SARReversal',
    'SARTrailing',
    'SARADXCombo',
    'SARMultiTimeframe',
]
