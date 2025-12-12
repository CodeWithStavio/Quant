"""
Strategy Signal Mixin
=====================
Mixin class to add signal output capabilities to Jesse strategies.
"""

from typing import Optional
from signals.signal import Signal, SignalType
from signals.manager import SignalManager


class SignalMixin:
    """
    Mixin class to add signal output capabilities to Jesse strategies.

    Usage:
        class MyStrategy(Strategy, SignalMixin):
            def __init__(self):
                super().__init__()
                self.init_signals()  # Initialize signal system

            def go_long(self):
                # ... your logic ...
                self.emit_signal(SignalType.LONG_ENTRY)

    Note: This mixin assumes the strategy has standard Jesse Strategy attributes:
        - self.symbol
        - self.exchange
        - self.timeframe
        - self.price
        - self.close, self.open, self.high, self.low
        - self.position
        - self.balance
    """

    # Class-level signal manager (shared across strategy instances)
    _signal_manager: Optional[SignalManager] = None

    def init_signals(
        self,
        manager: Optional[SignalManager] = None,
        console: bool = True,
        file: bool = False,
        file_path: str = "./signals_output"
    ) -> None:
        """
        Initialize signal system.

        Args:
            manager: Existing SignalManager or None to create default
            console: Enable console output (if creating new manager)
            file: Enable file output (if creating new manager)
            file_path: File output directory
        """
        if manager:
            SignalMixin._signal_manager = manager
        elif SignalMixin._signal_manager is None:
            from signals.manager import create_signal_manager
            SignalMixin._signal_manager = create_signal_manager(
                console=console,
                file=file,
                file_path=file_path
            )

    @property
    def signal_manager(self) -> Optional[SignalManager]:
        """Get the signal manager"""
        return SignalMixin._signal_manager

    def emit_signal(
        self,
        signal_type: SignalType,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        quantity: Optional[float] = None,
        confidence: int = 50,
        **metadata
    ) -> Optional[Signal]:
        """
        Emit a trading signal.

        Args:
            signal_type: Type of signal
            entry_price: Entry price (defaults to self.price)
            stop_loss: Stop loss price
            take_profit: Take profit price
            quantity: Position size
            confidence: Signal confidence (0-100)
            **metadata: Additional metadata

        Returns:
            Signal object if emitted, None otherwise
        """
        if not SignalMixin._signal_manager:
            return None

        # Determine side based on signal type
        side = None
        if signal_type in (SignalType.LONG_ENTRY, SignalType.LONG_EXIT):
            side = "long"
        elif signal_type in (SignalType.SHORT_ENTRY, SignalType.SHORT_EXIT):
            side = "short"

        # Get strategy attributes
        strategy_id = getattr(self, 'strategy_id', 'UNKNOWN')
        strategy_name = getattr(self, 'strategy_name', self.__class__.__name__)

        signal = Signal(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            signal_type=signal_type,
            symbol=self.symbol,
            exchange=self.exchange,
            timeframe=self.timeframe,
            price=self.price,
            entry_price=entry_price or self.price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            side=side,
            confidence=confidence,
            metadata=metadata
        )

        SignalMixin._signal_manager.send(signal)
        return signal

    def emit_long_entry(
        self,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        quantity: Optional[float] = None,
        confidence: int = 50,
        **metadata
    ) -> Optional[Signal]:
        """Emit long entry signal"""
        return self.emit_signal(
            SignalType.LONG_ENTRY,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            confidence=confidence,
            **metadata
        )

    def emit_short_entry(
        self,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        quantity: Optional[float] = None,
        confidence: int = 50,
        **metadata
    ) -> Optional[Signal]:
        """Emit short entry signal"""
        return self.emit_signal(
            SignalType.SHORT_ENTRY,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            confidence=confidence,
            **metadata
        )

    def emit_exit(
        self,
        exit_type: SignalType = SignalType.LONG_EXIT,
        **metadata
    ) -> Optional[Signal]:
        """Emit exit signal"""
        return self.emit_signal(exit_type, **metadata)

    def emit_stop_loss(self, **metadata) -> Optional[Signal]:
        """Emit stop loss hit signal"""
        return self.emit_signal(SignalType.STOP_LOSS_HIT, **metadata)

    def emit_take_profit(self, **metadata) -> Optional[Signal]:
        """Emit take profit hit signal"""
        return self.emit_signal(SignalType.TAKE_PROFIT_HIT, **metadata)

    def emit_trailing_stop_update(
        self,
        new_stop: float,
        **metadata
    ) -> Optional[Signal]:
        """Emit trailing stop update signal"""
        return self.emit_signal(
            SignalType.TRAILING_STOP_UPDATE,
            stop_loss=new_stop,
            **metadata
        )


class SignalStrategy:
    """
    Base strategy class with signal support pre-configured.

    Inherit from this along with jesse.strategies.Strategy:

        from jesse.strategies import Strategy
        from signals.strategy_mixin import SignalStrategy

        class MyStrategy(Strategy, SignalStrategy):
            def __init__(self):
                super().__init__()
                self.setup_signals()  # Initializes with defaults

            def go_long(self):
                entry = self.price
                stop = self.price - (self.atr * 2)
                qty = self.position_size(entry)
                self.buy = qty, entry
                self.stop_loss = qty, stop

                # Emit signal
                self.emit_long_entry(stop_loss=stop, quantity=qty)
    """

    def setup_signals(
        self,
        console: bool = True,
        file: bool = True,
        telegram_token: str = "",
        telegram_chats: list = None,
        discord_webhooks: list = None
    ) -> None:
        """Setup signal outputs"""
        from signals.manager import create_signal_manager

        manager = create_signal_manager(
            console=console,
            file=file,
            telegram_token=telegram_token,
            telegram_chats=telegram_chats or [],
            discord_webhooks=discord_webhooks or []
        )

        # Store on instance
        self._signal_manager = manager

    @property
    def signal_manager(self) -> Optional[SignalManager]:
        return getattr(self, '_signal_manager', None)

    def emit_signal(self, signal_type: SignalType, **kwargs) -> Optional[Signal]:
        """Emit a signal through the manager"""
        if not self.signal_manager:
            return None

        strategy_id = getattr(self, 'strategy_id', 'UNKNOWN')
        strategy_name = getattr(self, 'strategy_name', self.__class__.__name__)

        side = None
        if signal_type in (SignalType.LONG_ENTRY, SignalType.LONG_EXIT):
            side = "long"
        elif signal_type in (SignalType.SHORT_ENTRY, SignalType.SHORT_EXIT):
            side = "short"

        signal = Signal(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            signal_type=signal_type,
            symbol=self.symbol,
            exchange=self.exchange,
            timeframe=self.timeframe,
            price=self.price,
            side=side,
            **kwargs
        )

        self.signal_manager.send(signal)
        return signal

    def emit_long_entry(self, **kwargs) -> Optional[Signal]:
        return self.emit_signal(SignalType.LONG_ENTRY, **kwargs)

    def emit_short_entry(self, **kwargs) -> Optional[Signal]:
        return self.emit_signal(SignalType.SHORT_ENTRY, **kwargs)
