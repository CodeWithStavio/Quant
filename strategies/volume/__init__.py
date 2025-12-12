"""
Volume-Based Strategies
-----------------------
Strategies using volume analysis and volume-based indicators.

OBV (On-Balance Volume):
- VOL_001: OBV Trend Strategy
- VOL_002: OBV Divergence Strategy

VWAP (Volume Weighted Average Price):
- VOL_003: VWAP Bounce
- VOL_004: VWAP Bands

Volume Profile:
- VOL_005: Volume Breakout
- VOL_006: Volume Confirmation
- VOL_007: Volume Climax

Money Flow:
- VOL_008: MFI Overbought/Oversold
- VOL_009: Chaikin Money Flow
- VOL_010: Accumulation/Distribution

Advanced Volume:
- VOL_011: Force Index
- VOL_012: Ease of Movement
- VOL_013: Volume Rate of Change
- VOL_014: VPVR (Volume Profile Visible Range)
- VOL_015: Volume Weighted RSI
"""

from .vol_001_obv_trend import OBVTrend
from .vol_002_obv_divergence import OBVDivergence
from .vol_003_vwap_bounce import VWAPBounce
from .vol_004_vwap_bands import VWAPBands
from .vol_005_volume_breakout import VolumeBreakout
from .vol_006_volume_confirm import VolumeConfirmation
from .vol_007_volume_climax import VolumeClimax
from .vol_008_mfi import MFIStrategy
from .vol_009_cmf import CMFStrategy
from .vol_010_ad import ADStrategy
from .vol_011_force_index import ForceIndex
from .vol_012_eom import EaseOfMovement
from .vol_013_vroc import VolumeROC
from .vol_014_volume_profile import VolumeProfile
from .vol_015_vw_rsi import VolumeWeightedRSI

__all__ = [
    'OBVTrend',
    'OBVDivergence',
    'VWAPBounce',
    'VWAPBands',
    'VolumeBreakout',
    'VolumeConfirmation',
    'VolumeClimax',
    'MFIStrategy',
    'CMFStrategy',
    'ADStrategy',
    'ForceIndex',
    'EaseOfMovement',
    'VolumeROC',
    'VolumeProfile',
    'VolumeWeightedRSI',
]
