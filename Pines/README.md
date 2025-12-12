# TradingView Pine Script Strategy Library

A comprehensive collection of **54 Pine Script v5 strategies** for TradingView, optimized for **MES/MNQ futures** and **crypto scalping/intraday trading**.

## Overview

All strategies are:
- **Pine Script v5** - Latest syntax
- **Copy-paste ready** - Just paste into TradingView Pine Editor
- **Futures optimized** - $0.62 commission per contract
- **RTH filtered** - Optional Regular Trading Hours filter
- **Alert enabled** - Built-in alertcondition() for notifications

## Target Instruments

| Symbol | Description |
|--------|-------------|
| MES1! | Micro E-mini S&P 500 Continuous |
| MNQ1! | Micro E-mini Nasdaq-100 Continuous |
| ES1! | E-mini S&P 500 |
| NQ1! | E-mini Nasdaq-100 |
| BTCUSDT | Bitcoin (crypto) |
| ETHUSDT | Ethereum (crypto) |

## Directory Structure

```
Pines/
├── 01_moving_averages/     # 8 strategies
├── 02_rsi/                 # 5 strategies
├── 03_macd/                # 5 strategies
├── 04_bollinger_bands/     # 5 strategies
├── 05_supertrend_atr/      # 4 strategies
├── 06_stochastic/          # 2 strategies
├── 07_ichimoku/            # 2 strategies
├── 08_vwap/                # 2 strategies
├── 09_pivot_points/        # 2 strategies
├── 10_donchian/            # 1 strategy
├── 11_adx/                 # 1 strategy
├── 12_volume/              # 3 strategies
├── 13_candlestick/         # 3 strategies
├── 14_breakout/            # 3 strategies
├── 15_mean_reversion/      # 2 strategies
├── 16_session/             # 2 strategies
├── 17_confluence/          # 2 strategies
└── 18_scalping/            # 2 strategies
```

## Strategy Categories

### 01. Moving Averages (8)
| ID | Name | Complexity |
|----|------|------------|
| PINE_MA_001 | EMA Crossover | 1 |
| PINE_MA_002 | Triple EMA | 2 |
| PINE_MA_003 | Hull MA | 2 |
| PINE_MA_004 | VWMA | 2 |
| PINE_MA_005 | KAMA (Kaufman Adaptive) | 3 |
| PINE_MA_006 | ZLEMA (Zero Lag) | 2 |
| PINE_MA_007 | MA Ribbon | 3 |
| PINE_MA_008 | GMMA (Guppy Multiple MA) | 4 |

### 02. RSI (5)
| ID | Name | Complexity |
|----|------|------------|
| PINE_RSI_001 | RSI Overbought/Oversold | 1 |
| PINE_RSI_002 | RSI Divergence | 5 |
| PINE_RSI_003 | RSI + MA Filter | 2 |
| PINE_RSI_004 | Connors RSI | 4 |
| PINE_RSI_005 | RSI Range Shift | 3 |

### 03. MACD (5)
| ID | Name | Complexity |
|----|------|------------|
| PINE_MACD_001 | MACD Crossover | 1 |
| PINE_MACD_002 | MACD Zero Line Cross | 1 |
| PINE_MACD_003 | MACD Histogram Reversal | 2 |
| PINE_MACD_004 | MACD + RSI Combo | 3 |
| PINE_MACD_005 | Elder Impulse System | 4 |

### 04. Bollinger Bands (5)
| ID | Name | Complexity |
|----|------|------------|
| PINE_BB_001 | BB Bounce | 2 |
| PINE_BB_002 | BB Breakout | 2 |
| PINE_BB_003 | BB Squeeze | 3 |
| PINE_BB_004 | BB %B Strategy | 2 |
| PINE_BB_005 | Double Bollinger Bands | 3 |

### 05. SuperTrend/ATR (4)
| ID | Name | Complexity |
|----|------|------------|
| PINE_ST_001 | SuperTrend | 2 |
| PINE_ST_002 | SuperTrend + ADX Filter | 3 |
| PINE_ST_003 | ATR Trailing Stop | 3 |
| PINE_ST_004 | Chandelier Exit | 3 |

### 06. Stochastic (2)
| ID | Name | Complexity |
|----|------|------------|
| PINE_STOCH_001 | Stochastic Crossover | 1 |
| PINE_STOCH_002 | Stochastic RSI | 2 |

### 07. Ichimoku (2)
| ID | Name | Complexity |
|----|------|------------|
| PINE_ICH_001 | Cloud Breakout | 3 |
| PINE_ICH_002 | TK Cross | 2 |

### 08. VWAP (2)
| ID | Name | Complexity |
|----|------|------------|
| PINE_VWAP_001 | VWAP Crossover | 1 |
| PINE_VWAP_002 | VWAP Bands | 3 |

### 09. Pivot Points (2)
| ID | Name | Complexity |
|----|------|------------|
| PINE_PIV_001 | Classic Pivots | 2 |
| PINE_PIV_002 | Camarilla Pivots | 3 |

### 10. Donchian (1)
| ID | Name | Complexity |
|----|------|------------|
| PINE_DC_001 | Donchian Breakout (Turtle) | 2 |

### 11. ADX (1)
| ID | Name | Complexity |
|----|------|------------|
| PINE_ADX_001 | ADX + DI Crossover | 2 |

### 12. Volume (3)
| ID | Name | Complexity |
|----|------|------------|
| PINE_VOL_001 | Volume Breakout | 2 |
| PINE_VOL_002 | OBV Strategy | 2 |
| PINE_VOL_003 | MFI Strategy | 2 |

### 13. Candlestick (3)
| ID | Name | Complexity |
|----|------|------------|
| PINE_CNDL_001 | Engulfing Pattern | 2 |
| PINE_CNDL_002 | Hammer/Shooting Star | 2 |
| PINE_CNDL_003 | Doji Reversal | 2 |

### 14. Breakout (3)
| ID | Name | Complexity |
|----|------|------------|
| PINE_BO_001 | Opening Range Breakout | 3 |
| PINE_BO_002 | Previous Day H/L Breakout | 2 |
| PINE_BO_003 | NR7 Breakout | 3 |

### 15. Mean Reversion (2)
| ID | Name | Complexity |
|----|------|------------|
| PINE_MR_001 | RSI2 Mean Reversion | 2 |
| PINE_MR_002 | Z-Score Mean Reversion | 3 |

### 16. Session (2)
| ID | Name | Complexity |
|----|------|------------|
| PINE_SESS_001 | London/NY Session Breakout | 3 |
| PINE_SESS_002 | RTH Filter Strategy | 2 |

### 17. Confluence (2)
| ID | Name | Complexity |
|----|------|------------|
| PINE_CONF_001 | Triple Confirmation (EMA+RSI+MACD) | 4 |
| PINE_CONF_002 | VWAP + SuperTrend + RSI | 4 |

### 18. Scalping (2)
| ID | Name | Recommended TF |
|----|------|----------------|
| PINE_SCALP_001 | 1min EMA Scalp | 1m |
| PINE_SCALP_002 | VWAP Scalp | 5m |

## Usage

### Step 1: Open TradingView
Navigate to TradingView and open your chart.

### Step 2: Open Pine Editor
Click on "Pine Editor" at the bottom of the screen.

### Step 3: Copy Strategy Code
Open any `.pine` file from this library and copy the entire code.

### Step 4: Paste and Add to Chart
Paste the code into Pine Editor and click "Add to Chart".

### Step 5: Configure Inputs
Adjust strategy parameters in the Settings panel.

### Step 6: Set Up Alerts
Right-click on the chart and select "Add Alert" to configure notifications.

## Futures Settings

```pine
// Standard futures commission
commission_type=strategy.commission.cash_per_contract
commission_value=0.62  // Per side ($1.24 round trip)

// Default position sizing
default_qty_type=strategy.percent_of_equity
default_qty_value=100  // Full equity per trade
```

## Session Filter (RTH)

Most strategies include a Regular Trading Hours filter:
```pine
// RTH: 9:30 AM - 4:00 PM Eastern Time
rthSession = time(timeframe.period, '0930-1600:23456', 'America/New_York')
inRTH = not na(rthSession)
```

## Alert Configuration

All strategies include alert conditions:
```pine
alertcondition(longCondition, title='Long Signal', message='{{ticker}} LONG at {{close}}')
alertcondition(shortCondition, title='Short Signal', message='{{ticker}} SHORT at {{close}}')
```

### Webhook Message Variables
| Variable | Description |
|----------|-------------|
| {{ticker}} | Symbol name |
| {{close}} | Current price |
| {{time}} | Alert time |
| {{strategy.order.action}} | Buy/Sell |
| {{strategy.position_size}} | Position size |

## Recommended Timeframes

| Strategy Type | Timeframes |
|---------------|------------|
| Scalping | 1m, 5m |
| Intraday | 15m, 30m |
| Swing | 1h, 4h |
| Position | D, W |

## Risk Management

All strategies include:
- Stop loss (ATR-based or fixed points)
- Take profit targets
- Position sizing based on equity percentage

### Futures Stop Loss Guidelines
| Instrument | Conservative SL | Aggressive SL |
|------------|-----------------|---------------|
| MES | 10-15 points | 5-8 points |
| MNQ | 40-60 points | 20-35 points |

## License

MIT License - Free to use and modify.

## Disclaimer

These strategies are for educational purposes only. Past performance does not guarantee future results. Always backtest thoroughly and use proper risk management when trading.
