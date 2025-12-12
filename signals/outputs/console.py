"""
Console Output Handler
======================
Print signals to console/terminal.
"""

import sys
from datetime import datetime
from typing import TextIO
from signals.base_output import BaseOutput
from signals.signal import Signal, SignalType


class ConsoleOutput(BaseOutput):
    """
    Console output handler for printing signals to terminal.

    Features:
    - Colored output (optional)
    - JSON or formatted output
    - Configurable output stream
    """

    # ANSI color codes
    COLORS = {
        'reset': '\033[0m',
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
    }

    def __init__(
        self,
        name: str = "console",
        enabled: bool = True,
        use_colors: bool = True,
        json_format: bool = False,
        stream: TextIO = sys.stdout
    ):
        """
        Initialize console output.

        Args:
            name: Handler name
            enabled: Whether handler is active
            use_colors: Enable ANSI colors
            json_format: Output as JSON instead of formatted
            stream: Output stream (stdout, stderr, etc.)
        """
        super().__init__(name, enabled)
        self.use_colors = use_colors
        self.json_format = json_format
        self.stream = stream

    def _colorize(self, text: str, color: str) -> str:
        """Apply ANSI color to text"""
        if not self.use_colors:
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"

    def _get_signal_color(self, signal: Signal) -> str:
        """Get color based on signal type"""
        color_map = {
            SignalType.LONG_ENTRY: 'green',
            SignalType.SHORT_ENTRY: 'red',
            SignalType.LONG_EXIT: 'cyan',
            SignalType.SHORT_EXIT: 'cyan',
            SignalType.STOP_LOSS_HIT: 'yellow',
            SignalType.TAKE_PROFIT_HIT: 'blue',
            SignalType.TRAILING_STOP_UPDATE: 'white',
            SignalType.POSITION_UPDATE: 'white',
        }
        return color_map.get(signal.signal_type, 'white')

    def send(self, signal: Signal) -> bool:
        """Send signal to console"""
        if not self.should_send(signal):
            return False

        try:
            if self.json_format:
                output = signal.to_json()
            else:
                output = self._format_signal(signal)

            color = self._get_signal_color(signal)
            colored_output = self._colorize(output, color)

            print(colored_output, file=self.stream)
            self.stream.flush()
            return True

        except Exception as e:
            print(f"Console output error: {e}", file=sys.stderr)
            return False

    def _format_signal(self, signal: Signal) -> str:
        """Format signal for console output"""
        separator = "=" * 50
        lines = [
            separator,
            f"SIGNAL: {signal.signal_type.value}",
            separator,
            f"Strategy: {signal.strategy_name} ({signal.strategy_id})",
            f"Symbol:   {signal.symbol} @ {signal.exchange}",
            f"Timeframe: {signal.timeframe}",
            f"Price:    {signal.price:.8f}",
        ]

        if signal.entry_price:
            lines.append(f"Entry:    {signal.entry_price:.8f}")
        if signal.stop_loss:
            lines.append(f"SL:       {signal.stop_loss:.8f}")
        if signal.take_profit:
            lines.append(f"TP:       {signal.take_profit:.8f}")
        if signal.quantity:
            lines.append(f"Qty:      {signal.quantity:.8f}")
        if signal.side:
            lines.append(f"Side:     {signal.side.upper()}")

        rr = signal.calculate_risk_reward()
        if rr:
            lines.append(f"R:R:      1:{rr:.2f}")

        lines.extend([
            f"Confidence: {signal.confidence}%",
            f"Time:     {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            separator,
        ])

        return "\n".join(lines)
