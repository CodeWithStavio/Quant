"""
File Output Handler
===================
Save signals to JSON files.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from signals.base_output import BaseOutput
from signals.signal import Signal


class FileOutput(BaseOutput):
    """
    File output handler for persisting signals to disk.

    Features:
    - JSON format storage
    - Daily rotation
    - Single file or per-signal files
    - Automatic directory creation
    """

    def __init__(
        self,
        name: str = "file",
        enabled: bool = True,
        output_dir: str = "./signals_output",
        single_file: bool = True,
        filename: str = "signals.json",
        daily_rotation: bool = True,
        pretty_print: bool = True
    ):
        """
        Initialize file output.

        Args:
            name: Handler name
            enabled: Whether handler is active
            output_dir: Directory for output files
            single_file: Write all signals to one file vs separate files
            filename: Base filename (for single file mode)
            daily_rotation: Create new file each day
            pretty_print: Format JSON with indentation
        """
        super().__init__(name, enabled)
        self.output_dir = Path(output_dir)
        self.single_file = single_file
        self.filename = filename
        self.daily_rotation = daily_rotation
        self.pretty_print = pretty_print
        self._signals_buffer: List[dict] = []

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_filename(self) -> Path:
        """Get output filename (with date if rotating)"""
        if self.daily_rotation:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            base, ext = os.path.splitext(self.filename)
            return self.output_dir / f"{base}_{date_str}{ext}"
        return self.output_dir / self.filename

    def _get_signal_filename(self, signal: Signal) -> Path:
        """Get filename for individual signal file"""
        timestamp = signal.timestamp.strftime("%Y%m%d_%H%M%S_%f")
        return self.output_dir / f"signal_{signal.strategy_id}_{timestamp}.json"

    def send(self, signal: Signal) -> bool:
        """Save signal to file"""
        if not self.should_send(signal):
            return False

        try:
            signal_dict = signal.to_dict()
            indent = 2 if self.pretty_print else None

            if self.single_file:
                # Append to buffer and write
                self._signals_buffer.append(signal_dict)
                self._write_buffer()
            else:
                # Write individual file
                filepath = self._get_signal_filename(signal)
                with open(filepath, 'w') as f:
                    json.dump(signal_dict, f, indent=indent)

            return True

        except Exception as e:
            print(f"File output error: {e}")
            return False

    def _write_buffer(self) -> None:
        """Write signal buffer to file"""
        filepath = self._get_filename()
        indent = 2 if self.pretty_print else None

        # Load existing signals if file exists
        existing = []
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing = []

        # Combine and write
        all_signals = existing + self._signals_buffer
        with open(filepath, 'w') as f:
            json.dump(all_signals, f, indent=indent)

        self._signals_buffer = []

    def load_signals(self, date: Optional[datetime] = None) -> List[Signal]:
        """
        Load signals from file.

        Args:
            date: Specific date to load (uses current date if None)

        Returns:
            List of Signal objects
        """
        if date and self.daily_rotation:
            date_str = date.strftime("%Y-%m-%d")
            base, ext = os.path.splitext(self.filename)
            filepath = self.output_dir / f"{base}_{date_str}{ext}"
        else:
            filepath = self._get_filename()

        if not filepath.exists():
            return []

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return [Signal.from_dict(d) for d in data]
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading signals: {e}")
            return []

    def close(self) -> None:
        """Flush any remaining signals"""
        if self._signals_buffer:
            self._write_buffer()
