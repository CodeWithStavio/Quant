"""
Sentiment, On-Chain, and Crypto-Specific Strategies
----------------------------------------------------
32 strategies for cryptocurrency-focused trading.
"""

# Sentiment Proxy Strategies
from .sent_001_volatility_sentiment import VolatilitySentiment
from .sent_002_volume_sentiment import VolumeSentiment
from .sent_003_momentum_sentiment import MomentumSentiment
from .sent_004_fear_greed_proxy import FearGreedProxy
from .sent_005_market_breadth import MarketBreadth
from .sent_006_trend_strength import TrendStrengthSentiment
from .sent_007_reversal_sentiment import ReversalSentiment
from .sent_008_crowd_behavior import CrowdBehavior

# On-Chain Proxy Strategies
from .onchain_001_accumulation import AccumulationDetector
from .onchain_002_distribution import DistributionDetector
from .onchain_003_whale_activity import WhaleActivityProxy
from .onchain_004_holder_behavior import HolderBehaviorProxy
from .onchain_005_network_value import NetworkValueProxy
from .onchain_006_velocity import VelocityProxy
from .onchain_007_supply_shock import SupplyShockProxy
from .onchain_008_dormancy import DormancyProxy

# Crypto-Specific Strategies
from .crypto_001_funding_rate import FundingRateProxy
from .crypto_002_basis_trade import BasisTradeProxy
from .crypto_003_altcoin_season import AltcoinSeasonProxy
from .crypto_004_btc_dominance import BTCDominanceProxy
from .crypto_005_correlation import CorrelationBreakdown
from .crypto_006_volatility_regime import VolatilityRegime
from .crypto_007_weekend_effect import WeekendEffect
from .crypto_008_asian_session import AsianSession
from .crypto_009_london_session import LondonSession
from .crypto_010_ny_session import NYSession
from .crypto_011_halving_cycle import HalvingCycleProxy
from .crypto_012_market_cycle import MarketCyclePhase
from .crypto_013_defi_momentum import DeFiMomentum
from .crypto_014_layer1_rotation import Layer1Rotation
from .crypto_015_meme_momentum import MemeMomentum
from .crypto_016_stablecoin_flow import StablecoinFlowProxy

__all__ = [
    # Sentiment
    'VolatilitySentiment', 'VolumeSentiment', 'MomentumSentiment',
    'FearGreedProxy', 'MarketBreadth', 'TrendStrengthSentiment',
    'ReversalSentiment', 'CrowdBehavior',
    # On-Chain
    'AccumulationDetector', 'DistributionDetector', 'WhaleActivityProxy',
    'HolderBehaviorProxy', 'NetworkValueProxy', 'VelocityProxy',
    'SupplyShockProxy', 'DormancyProxy',
    # Crypto
    'FundingRateProxy', 'BasisTradeProxy', 'AltcoinSeasonProxy',
    'BTCDominanceProxy', 'CorrelationBreakdown', 'VolatilityRegime',
    'WeekendEffect', 'AsianSession', 'LondonSession', 'NYSession',
    'HalvingCycleProxy', 'MarketCyclePhase', 'DeFiMomentum',
    'Layer1Rotation', 'MemeMomentum', 'StablecoinFlowProxy',
]
