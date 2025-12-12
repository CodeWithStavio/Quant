"""
Jesse Routes Configuration
--------------------------
Define trading routes for backtesting and live trading.
"""

from jesse.enums import exchanges, timeframes

# Routes configuration
# Format: (exchange, symbol, timeframe, strategy_name)

routes = [
    # Example route - uncomment and modify as needed
    # (exchanges.BINANCE_PERPETUAL_FUTURES, 'BTC-USDT', timeframes.MINUTE_15, 'SMAcrossover'),
]

# Extra candles for multi-timeframe strategies
# Format: (exchange, symbol, timeframe)
extra_candles = [
    # Example - uncomment as needed
    # (exchanges.BINANCE_PERPETUAL_FUTURES, 'BTC-USDT', timeframes.HOUR_4),
    # (exchanges.BINANCE_PERPETUAL_FUTURES, 'BTC-USDT', timeframes.HOUR_1),
]
