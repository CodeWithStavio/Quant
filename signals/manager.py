"""
Signal Manager
==============
Central manager for coordinating signal outputs.
"""

import threading
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from signals.signal import Signal, SignalType
from signals.base_output import BaseOutput


class SignalManager:
    """
    Central manager for coordinating signal distribution across multiple outputs.

    Features:
    - Register multiple output handlers
    - Broadcast signals to all handlers
    - Async/parallel sending option
    - Signal history tracking
    - Handler enable/disable management
    """

    def __init__(
        self,
        outputs: Optional[List[BaseOutput]] = None,
        max_history: int = 1000,
        parallel_send: bool = True,
        max_workers: int = 5
    ):
        """
        Initialize signal manager.

        Args:
            outputs: Initial list of output handlers
            max_history: Maximum signals to keep in history
            parallel_send: Send to handlers in parallel
            max_workers: Thread pool size for parallel sending
        """
        self._outputs: Dict[str, BaseOutput] = {}
        self._history: List[Signal] = []
        self._max_history = max_history
        self._parallel_send = parallel_send
        self._max_workers = max_workers
        self._lock = threading.Lock()

        # Register initial outputs
        if outputs:
            for output in outputs:
                self.register(output)

    def register(self, output: BaseOutput) -> 'SignalManager':
        """
        Register an output handler.

        Args:
            output: Output handler to register

        Returns:
            Self for chaining
        """
        self._outputs[output.name] = output
        return self

    def unregister(self, name: str) -> 'SignalManager':
        """
        Unregister an output handler.

        Args:
            name: Name of handler to remove

        Returns:
            Self for chaining
        """
        if name in self._outputs:
            self._outputs[name].close()
            del self._outputs[name]
        return self

    def get_output(self, name: str) -> Optional[BaseOutput]:
        """Get output handler by name"""
        return self._outputs.get(name)

    def enable_output(self, name: str) -> None:
        """Enable an output handler"""
        if name in self._outputs:
            self._outputs[name].enabled = True

    def disable_output(self, name: str) -> None:
        """Disable an output handler"""
        if name in self._outputs:
            self._outputs[name].enabled = False

    def send(self, signal: Signal) -> Dict[str, bool]:
        """
        Send signal to all registered outputs.

        Args:
            signal: Signal to send

        Returns:
            Dictionary of handler_name -> success status
        """
        # Add to history
        with self._lock:
            self._history.append(signal)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        results = {}

        if self._parallel_send and len(self._outputs) > 1:
            # Parallel sending
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                futures = {
                    executor.submit(output.send, signal): name
                    for name, output in self._outputs.items()
                    if output.enabled
                }

                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        results[name] = future.result()
                    except Exception as e:
                        print(f"Error in {name}: {e}")
                        results[name] = False
        else:
            # Sequential sending
            for name, output in self._outputs.items():
                if output.enabled:
                    try:
                        results[name] = output.send(signal)
                    except Exception as e:
                        print(f"Error in {name}: {e}")
                        results[name] = False

        return results

    def send_batch(self, signals: List[Signal]) -> int:
        """
        Send multiple signals.

        Args:
            signals: List of signals to send

        Returns:
            Total number of successful sends
        """
        total = 0
        for signal in signals:
            results = self.send(signal)
            total += sum(1 for success in results.values() if success)
        return total

    def get_history(
        self,
        limit: Optional[int] = None,
        signal_type: Optional[SignalType] = None,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> List[Signal]:
        """
        Get signal history with optional filtering.

        Args:
            limit: Maximum signals to return
            signal_type: Filter by signal type
            strategy_id: Filter by strategy ID
            symbol: Filter by symbol

        Returns:
            List of matching signals
        """
        with self._lock:
            signals = self._history.copy()

        # Apply filters
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        if strategy_id:
            signals = [s for s in signals if s.strategy_id == strategy_id]
        if symbol:
            signals = [s for s in signals if s.symbol == symbol]

        # Apply limit (most recent first)
        if limit:
            signals = signals[-limit:]

        return signals

    def clear_history(self) -> None:
        """Clear signal history"""
        with self._lock:
            self._history.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get signal statistics.

        Returns:
            Dictionary with stats
        """
        with self._lock:
            signals = self._history.copy()

        if not signals:
            return {
                'total_signals': 0,
                'by_type': {},
                'by_strategy': {},
                'by_symbol': {},
            }

        by_type: Dict[str, int] = {}
        by_strategy: Dict[str, int] = {}
        by_symbol: Dict[str, int] = {}

        for signal in signals:
            # By type
            type_key = signal.signal_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # By strategy
            by_strategy[signal.strategy_id] = by_strategy.get(signal.strategy_id, 0) + 1

            # By symbol
            by_symbol[signal.symbol] = by_symbol.get(signal.symbol, 0) + 1

        return {
            'total_signals': len(signals),
            'by_type': by_type,
            'by_strategy': by_strategy,
            'by_symbol': by_symbol,
            'registered_outputs': list(self._outputs.keys()),
            'enabled_outputs': [n for n, o in self._outputs.items() if o.enabled],
        }

    def close(self) -> None:
        """Close all output handlers"""
        for output in self._outputs.values():
            try:
                output.close()
            except Exception as e:
                print(f"Error closing {output.name}: {e}")
        self._outputs.clear()

    def __enter__(self) -> 'SignalManager':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


# Convenience factory function
def create_signal_manager(
    console: bool = True,
    file: bool = False,
    file_path: str = "./signals_output",
    telegram_token: str = "",
    telegram_chats: Optional[List[str]] = None,
    discord_webhooks: Optional[List[str]] = None,
    api_endpoint: str = "",
    email_config: Optional[Dict[str, Any]] = None
) -> SignalManager:
    """
    Factory function to create a configured SignalManager.

    Args:
        console: Enable console output
        file: Enable file output
        file_path: Directory for file output
        telegram_token: Telegram bot token
        telegram_chats: Telegram chat IDs
        discord_webhooks: Discord webhook URLs
        api_endpoint: REST API endpoint
        email_config: Email configuration dict

    Returns:
        Configured SignalManager
    """
    from signals.outputs.console import ConsoleOutput
    from signals.outputs.file import FileOutput
    from signals.outputs.telegram import TelegramOutput
    from signals.outputs.discord import DiscordOutput
    from signals.outputs.api import APIOutput
    from signals.outputs.email import EmailOutput

    manager = SignalManager()

    if console:
        manager.register(ConsoleOutput())

    if file:
        manager.register(FileOutput(output_dir=file_path))

    if telegram_token and telegram_chats:
        manager.register(TelegramOutput(
            bot_token=telegram_token,
            chat_ids=telegram_chats
        ))

    if discord_webhooks:
        manager.register(DiscordOutput(webhook_urls=discord_webhooks))

    if api_endpoint:
        manager.register(APIOutput(endpoint=api_endpoint))

    if email_config:
        manager.register(EmailOutput(**email_config))

    return manager
