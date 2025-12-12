"""
Multi-Timeframe and Machine Learning-Inspired Strategies
---------------------------------------------------------
Strategies using multi-timeframe analysis and ML-like concepts.

Multi-Timeframe:
- MTF_001: Dual TF Confirmation
- MTF_002: Triple TF Alignment
- MTF_003: TF Divergence
- MTF_004: TF Momentum Cascade
- MTF_005: TF Trend Sync
- MTF_006: TF Support/Resistance
- MTF_007: TF Volume Confirmation
- MTF_008: TF Volatility Filter
- MTF_009: TF Oscillator Confluence
- MTF_010: TF Price Action

ML-Inspired (Statistical):
- ML_001: Pattern Recognition
- ML_002: Regime Detection
- ML_003: Adaptive Moving Average
- ML_004: Dynamic Stop Loss
- ML_005: Probability Based Entry
- ML_006: Clustering Zones
- ML_007: Feature Momentum
- ML_008: Ensemble Signals
- ML_009: Adaptive RSI
- ML_010: Self-Optimizing Parameters
- ML_011: Statistical Arbitrage
"""

from .mtf_001_dual_tf import DualTFConfirmation
from .mtf_002_triple_tf import TripleTFAlignment
from .mtf_003_divergence import TFDivergence
from .mtf_004_momentum import TFMomentumCascade
from .mtf_005_trend_sync import TFTrendSync
from .mtf_006_sr import TFSupportResistance
from .mtf_007_volume import TFVolumeConfirmation
from .mtf_008_volatility import TFVolatilityFilter
from .mtf_009_oscillator import TFOscillatorConfluence
from .mtf_010_price_action import TFPriceAction
from .ml_001_pattern import PatternRecognition
from .ml_002_regime import RegimeDetection
from .ml_003_adaptive_ma import AdaptiveMA
from .ml_004_dynamic_stop import DynamicStopLoss
from .ml_005_probability import ProbabilityEntry
from .ml_006_clustering import ClusteringZones
from .ml_007_feature_momentum import FeatureMomentum
from .ml_008_ensemble import EnsembleSignals
from .ml_009_adaptive_rsi import AdaptiveRSI
from .ml_010_self_optimize import SelfOptimizing
from .ml_011_stat_arb import StatisticalArbitrage

__all__ = [
    'DualTFConfirmation',
    'TripleTFAlignment',
    'TFDivergence',
    'TFMomentumCascade',
    'TFTrendSync',
    'TFSupportResistance',
    'TFVolumeConfirmation',
    'TFVolatilityFilter',
    'TFOscillatorConfluence',
    'TFPriceAction',
    'PatternRecognition',
    'RegimeDetection',
    'AdaptiveMA',
    'DynamicStopLoss',
    'ProbabilityEntry',
    'ClusteringZones',
    'FeatureMomentum',
    'EnsembleSignals',
    'AdaptiveRSI',
    'SelfOptimizing',
    'StatisticalArbitrage',
]
