#!/usr/bin/env python3
"""
Test script to verify Jesse strategy implementations.
Creates mock Jesse modules and tests all strategy imports.
"""

import sys
import os
import importlib.util
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# Add the project root to path
sys.path.insert(0, '/home/user/Quant')

# ============================================================
# Mock Jesse's Strategy class since Jesse isn't installed
# ============================================================
class MockStrategy:
    """Mock Strategy class to test strategy implementations"""

    def __init__(self):
        self.position = None
        self.is_long = False
        self.is_short = False
        self.index = 100
        self._candles = np.array([
            [1700000000000, 50000, 50100, 49900, 50050, 1000],
            [1700000060000, 50050, 50150, 49950, 50100, 1100],
            [1700000120000, 50100, 50200, 50000, 50150, 1200],
        ] * 100)
        self._hp = {
            'fast_period': 10,
            'slow_period': 50,
            'atr_multiplier_sl': 2.0,
            'atr_multiplier_tp': 3.0,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'bb_period': 20,
            'bb_std': 2.0,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
        }
        self.buy = None
        self.sell = None
        self.stop_loss = None
        self.take_profit = None

    @property
    def candles(self):
        return self._candles

    @property
    def close(self):
        return self._candles[-1, 2]

    @property
    def open(self):
        return self._candles[-1, 1]

    @property
    def high(self):
        return self._candles[-1, 3]

    @property
    def low(self):
        return self._candles[-1, 4]

    @property
    def volume(self):
        return self._candles[-1, 5]

    @property
    def price(self):
        return self.close

    @property
    def symbol(self):
        return "BTC-USDT"

    @property
    def exchange(self):
        return "Binance Futures"

    @property
    def timeframe(self):
        return "1h"

    @property
    def balance(self):
        return 10000.0

    @property
    def hp(self):
        return self._hp

    def liquidate(self):
        pass


# ============================================================
# Mock jesse.utils module
# ============================================================
class MockUtils:
    @staticmethod
    def size_to_qty(size: float, price: float, precision: int = 8) -> float:
        if price == 0:
            return 0
        return round(size / price, precision)

    @staticmethod
    def qty_to_size(qty: float, price: float) -> float:
        return qty * price

    @staticmethod
    def risk_to_qty(capital: float, risk_per_trade: float, entry: float, stop: float) -> float:
        if entry == stop:
            return 0
        risk_amount = capital * risk_per_trade
        risk_per_unit = abs(entry - stop)
        return risk_amount / risk_per_unit


# ============================================================
# Mock jesse.indicators module
# ============================================================
class MockIndicators:
    """Mock all Jesse indicator functions"""

    @staticmethod
    def sma(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def ema(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def rsi(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50
        return 50.0

    @staticmethod
    def macd(candles, fast_period=12, slow_period=26, signal_period=9, source_type='close', sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 100, np.ones(n) * 80, np.ones(n) * 20
        return 100.0, 80.0, 20.0

    @staticmethod
    def bollinger_bands(candles, period=20, devup=2.0, devdn=2.0, source_type='close', sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 51000, np.ones(n) * 50000, np.ones(n) * 49000
        return 51000.0, 50000.0, 49000.0

    @staticmethod
    def atr(candles, period=14, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 500
        return 500.0

    @staticmethod
    def stoch(candles, fastk_period=14, slowk_period=3, slowd_period=3, sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 50, np.ones(n) * 50
        return 50.0, 50.0

    @staticmethod
    def adx(candles, period=14, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 25
        return 25.0

    @staticmethod
    def supertrend(candles, period=10, factor=3.0, sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 49500, np.ones(n) * 1
        return 49500.0, 1

    @staticmethod
    def ichimoku_cloud(candles, conversion_line_period=9, base_line_period=26, lagging_span_period=52, displacement=26):
        return 50000, 50000, 50000, 50000, 50000, True

    @staticmethod
    def vwap(candles, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def cci(candles, period=20, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def willr(candles, period=14, sequential=False):
        if sequential:
            return np.ones(len(candles)) * -50
        return -50.0

    @staticmethod
    def obv(candles, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 1000000
        return 1000000.0

    @staticmethod
    def mfi(candles, period=14, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50
        return 50.0

    @staticmethod
    def psar(candles, acceleration=0.02, maximum=0.2, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 49500
        return 49500.0

    @staticmethod
    def donchian(candles, period=20, sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 51000, np.ones(n) * 50000, np.ones(n) * 49000
        return 51000.0, 50000.0, 49000.0

    @staticmethod
    def keltner(candles, period=20, multiplier=2.0, sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 51000, np.ones(n) * 50000, np.ones(n) * 49000
        return 51000.0, 50000.0, 49000.0

    @staticmethod
    def dema(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def tema(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def hma(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def kama(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def wma(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def vwma(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def zlema(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def alma(candles, period=14, offset=0.85, sigma=6, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def trix(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def roc(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def mom(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def cmo(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def aroon(candles, period=14, sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 50, np.ones(n) * 50
        return 50.0, 50.0

    @staticmethod
    def aroonosc(candles, period=14, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def pivot(candles, sequential=False):
        return 50000.0, 51000.0, 49000.0, 52000.0, 48000.0

    @staticmethod
    def fisher(candles, period=9, sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 0, np.ones(n) * 0
        return 0.0, 0.0

    @staticmethod
    def wad(candles, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def ao(candles, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def chop(candles, period=14, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50
        return 50.0

    @staticmethod
    def di(candles, period=14, sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 25, np.ones(n) * 25
        return 25.0, 25.0

    @staticmethod
    def dm(candles, period=14, sequential=False):
        if sequential:
            n = len(candles)
            return np.ones(n) * 100, np.ones(n) * 100
        return 100.0, 100.0

    @staticmethod
    def emv(candles, period=14, divisor=10000, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def efi(candles, period=13, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def ad(candles, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def adosc(candles, fast_period=3, slow_period=10, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def cmf(candles, period=20, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def pvi(candles, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 1000
        return 1000.0

    @staticmethod
    def nvi(candles, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 1000
        return 1000.0

    @staticmethod
    def uo(candles, short_period=7, medium_period=14, long_period=28, sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50
        return 50.0

    @staticmethod
    def stddev(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 100
        return 100.0

    @staticmethod
    def var(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 10000
        return 10000.0

    @staticmethod
    def linearreg(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def linearreg_slope(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def linearreg_angle(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def linearreg_intercept(candles, period=14, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 50000
        return 50000.0

    @staticmethod
    def correlation(series1, series2, period=14, sequential=False):
        if sequential:
            return np.ones(len(series1)) * 0.5
        return 0.5

    @staticmethod
    def beta(candles1, candles2, period=14, sequential=False):
        if sequential:
            return np.ones(len(candles1)) * 1.0
        return 1.0

    @staticmethod
    def high_pass_2_pole_iir(candles, period=48, source_type='close', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 0
        return 0.0

    @staticmethod
    def kaufmanstop(candles, period=22, mult=2.0, direction='long', sequential=False):
        if sequential:
            return np.ones(len(candles)) * 49000
        return 49000.0

    # Add any additional indicators as static methods
    def __getattr__(self, name):
        """Fallback for any missing indicator - return a mock function"""
        def mock_indicator(*args, **kwargs):
            sequential = kwargs.get('sequential', False)
            if sequential and len(args) > 0:
                n = len(args[0])
                return np.ones(n) * 50
            return 50.0
        return mock_indicator


# ============================================================
# Create mock jesse module structure
# ============================================================
class MockJesseStrategies:
    Strategy = MockStrategy


class MockJesse:
    strategies = MockJesseStrategies()
    utils = MockUtils()


# Create indicator instance
mock_indicators = MockIndicators()

# Inject mock jesse modules into sys.modules
sys.modules['jesse'] = MockJesse()
sys.modules['jesse.strategies'] = MockJesseStrategies()
sys.modules['jesse.utils'] = MockUtils
sys.modules['jesse.indicators'] = mock_indicators

# Also create the module with Strategy attribute for import
import types
jesse_module = types.ModuleType('jesse')
jesse_module.strategies = MockJesseStrategies()
jesse_module.utils = MockUtils()
sys.modules['jesse'] = jesse_module

jesse_strategies_module = types.ModuleType('jesse.strategies')
jesse_strategies_module.Strategy = MockStrategy
sys.modules['jesse.strategies'] = jesse_strategies_module

jesse_utils_module = types.ModuleType('jesse.utils')
jesse_utils_module.size_to_qty = MockUtils.size_to_qty
jesse_utils_module.qty_to_size = MockUtils.qty_to_size
jesse_utils_module.risk_to_qty = MockUtils.risk_to_qty
sys.modules['jesse.utils'] = jesse_utils_module


def find_strategy_files(base_path: str) -> List[Path]:
    """Find all strategy Python files"""
    strategies_path = Path(base_path) / 'strategies'
    strategy_files = []

    for py_file in strategies_path.rglob('*.py'):
        if py_file.name != '__init__.py' and not py_file.name.startswith('base'):
            strategy_files.append(py_file)

    return sorted(strategy_files)


def test_strategy_file(file_path: Path) -> Dict[str, Any]:
    """Test a single strategy file"""
    result = {
        'file': str(file_path),
        'status': 'unknown',
        'error': None,
        'class_name': None,
        'has_hyperparameters': False,
        'has_should_long': False,
        'has_should_short': False,
    }

    try:
        # Load the module
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        module = importlib.util.module_from_spec(spec)

        # Try to execute the module
        spec.loader.exec_module(module)

        # Find strategy class (class that inherits from Strategy)
        strategy_class = None
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and name != 'Strategy' and name != 'BaseStrategy':
                # Check if it looks like a strategy class
                if hasattr(obj, 'should_long') or hasattr(obj, 'go_long'):
                    strategy_class = obj
                    result['class_name'] = name
                    break

        if strategy_class is None:
            result['status'] = 'warning'
            result['error'] = 'No strategy class found'
            return result

        # Try to instantiate
        instance = strategy_class()

        # Check for required methods
        result['has_hyperparameters'] = hasattr(instance, 'hyperparameters')
        result['has_should_long'] = hasattr(instance, 'should_long') and callable(getattr(instance, 'should_long'))
        result['has_should_short'] = hasattr(instance, 'should_short') and callable(getattr(instance, 'should_short'))

        # Check hyperparameters property
        if result['has_hyperparameters']:
            try:
                hp = instance.hyperparameters
                if isinstance(hp, list):
                    result['hyperparameters_count'] = len(hp)
            except Exception as e:
                result['hyperparameters_error'] = str(e)

        result['status'] = 'ok'

    except SyntaxError as e:
        result['status'] = 'error'
        result['error'] = f'Syntax error: {e}'
    except ImportError as e:
        result['status'] = 'error'
        result['error'] = f'Import error: {e}'
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f'{type(e).__name__}: {e}'

    return result


def main():
    print("=" * 60)
    print("Jesse Strategy Implementation Test")
    print("=" * 60)
    print()

    base_path = '/home/user/Quant'
    strategy_files = find_strategy_files(base_path)

    print(f"Found {len(strategy_files)} strategy files")
    print()

    results = {
        'ok': [],
        'warning': [],
        'error': []
    }

    for file_path in strategy_files:
        result = test_strategy_file(file_path)
        results[result['status']].append(result)

        # Print status
        status_symbol = {'ok': '✓', 'warning': '⚠', 'error': '✗'}.get(result['status'], '?')
        relative_path = file_path.relative_to(base_path)

        if result['status'] == 'ok':
            print(f"  {status_symbol} {relative_path}")
        else:
            print(f"  {status_symbol} {relative_path}")
            if result['error']:
                print(f"      └─ {result['error']}")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  ✓ Passed:   {len(results['ok'])}")
    print(f"  ⚠ Warnings: {len(results['warning'])}")
    print(f"  ✗ Errors:   {len(results['error'])}")
    print(f"  Total:      {len(strategy_files)}")
    print()

    if results['error']:
        print("Errors found:")
        for r in results['error'][:10]:  # Show first 10 errors
            print(f"  - {Path(r['file']).name}: {r['error']}")
        if len(results['error']) > 10:
            print(f"  ... and {len(results['error']) - 10} more errors")

    return len(results['error']) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
