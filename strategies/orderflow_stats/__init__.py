"""
Order Flow and Statistical Strategies
-------------------------------------
18 strategies based on order flow analysis and statistical methods.
"""

# Order Flow Strategies
from .of_001_volume_imbalance import VolumeImbalance
from .of_002_delta_momentum import DeltaMomentum
from .of_003_absorption import AbsorptionDetector
from .of_004_exhaustion import ExhaustionDetector
from .of_005_footprint import FootprintProxy
from .of_006_liquidity_grab import LiquidityGrab
from .of_007_iceberg import IcebergDetector
from .of_008_sweep import SweepDetector

# Statistical Strategies
from .stat_001_zscore import ZScoreMeanReversion
from .stat_002_percentile import PercentileRank
from .stat_003_regression import RegressionChannel
from .stat_004_variance import VarianceBreakout
from .stat_005_correlation import CorrelationRegime
from .stat_006_distribution import DistributionAnalysis
from .stat_007_outlier import OutlierDetector
from .stat_008_kalman import KalmanFilter
from .stat_009_hurst import HurstExponent
from .stat_010_entropy import EntropyAnalysis

__all__ = [
    # Order Flow
    'VolumeImbalance', 'DeltaMomentum', 'AbsorptionDetector',
    'ExhaustionDetector', 'FootprintProxy', 'LiquidityGrab',
    'IcebergDetector', 'SweepDetector',
    # Statistical
    'ZScoreMeanReversion', 'PercentileRank', 'RegressionChannel',
    'VarianceBreakout', 'CorrelationRegime', 'DistributionAnalysis',
    'OutlierDetector', 'KalmanFilter', 'HurstExponent', 'EntropyAnalysis',
]
