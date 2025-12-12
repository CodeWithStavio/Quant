"""
Jesse Configuration File
------------------------
Configuration for Jesse crypto trading framework strategies.
"""

# Trading configuration
config = {
    # Exchange settings
    'exchange': 'Binance Perpetual Futures',

    # Default risk settings
    'risk_per_trade': 0.02,  # 2% risk per trade
    'max_position_size': 0.1,  # 10% max position
    'max_open_positions': 3,

    # Default timeframe
    'default_timeframe': '15m',

    # Backtesting settings
    'starting_balance': 10000,
    'fee_rate': 0.0004,  # 0.04% maker/taker

    # Signal output settings
    'signal_output': {
        'console': True,
        'json_file': True,
        'telegram': False,
        'discord': False,
    },

    # Logging
    'log_level': 'INFO',
}

# Supported symbols
symbols = [
    'BTC-USDT',
    'ETH-USDT',
    'BNB-USDT',
    'SOL-USDT',
    'XRP-USDT',
    'ADA-USDT',
    'DOGE-USDT',
    'AVAX-USDT',
    'DOT-USDT',
    'MATIC-USDT',
]

# Supported timeframes
timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d']

# Strategy categories
strategy_categories = [
    'moving_averages',
    'momentum_oscillators',
    'macd',
    'bollinger_bands',
    'keltner_channels',
    'donchian_channels',
    'atr_volatility',
    'volume',
    'ichimoku',
    'adx_dmi',
    'parabolic_sar',
    'pivot_points',
    'fibonacci',
    'candlestick_patterns',
    'price_action',
    'mean_reversion',
    'breakout',
    'trend_following',
    'scalping',
    'multi_timeframe',
    'machine_learning',
    'sentiment',
    'on_chain',
    'crypto_specific',
    'order_flow',
    'statistical',
    'seasonality_time',
    'risk_parity',
    'composite',
    'advanced_exotic',
]
