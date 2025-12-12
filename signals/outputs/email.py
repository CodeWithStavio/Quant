"""
Email Output Handler
====================
Send signals via email (SMTP).
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from signals.base_output import BaseOutput
from signals.signal import Signal, SignalType


class EmailOutput(BaseOutput):
    """
    Email output handler for sending signals via SMTP.

    Features:
    - HTML and plain text formats
    - Multiple recipients
    - TLS/SSL support
    - Configurable SMTP settings

    Common SMTP settings:
    - Gmail: smtp.gmail.com:587 (use app password)
    - Outlook: smtp.office365.com:587
    - Yahoo: smtp.mail.yahoo.com:587
    """

    def __init__(
        self,
        name: str = "email",
        enabled: bool = True,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        from_address: str = "",
        to_addresses: Optional[List[str]] = None,
        use_tls: bool = True,
        use_ssl: bool = False,
        subject_prefix: str = "[Trading Signal]"
    ):
        """
        Initialize email output.

        Args:
            name: Handler name
            enabled: Whether handler is active
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_address: Sender email address
            to_addresses: List of recipient addresses
            use_tls: Use STARTTLS
            use_ssl: Use SSL (mutually exclusive with TLS)
            subject_prefix: Email subject prefix
        """
        super().__init__(name, enabled)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_address = from_address
        self.to_addresses = to_addresses or []
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.subject_prefix = subject_prefix

    def _get_subject(self, signal: Signal) -> str:
        """Generate email subject"""
        type_str = signal.signal_type.value.replace('_', ' ')
        return f"{self.subject_prefix} {type_str} - {signal.symbol}"

    def _build_html_body(self, signal: Signal) -> str:
        """Build HTML email body"""
        color_map = {
            SignalType.LONG_ENTRY: '#57F287',
            SignalType.SHORT_ENTRY: '#ED4245',
            SignalType.TAKE_PROFIT_HIT: '#5865F2',
            SignalType.STOP_LOSS_HIT: '#FFFF00',
        }
        header_color = color_map.get(signal.signal_type, '#95A5A6')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #f5f5f5; border-radius: 10px; overflow: hidden; }}
                .header {{ background: {header_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #ddd; }}
                .label {{ font-weight: bold; color: #666; }}
                .value {{ color: #333; font-family: monospace; }}
                .footer {{ padding: 15px; text-align: center; color: #999; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{signal.signal_type.value.replace('_', ' ')}</h1>
                    <h2>{signal.strategy_name}</h2>
                </div>
                <div class="content">
                    <div class="row">
                        <span class="label">Strategy ID</span>
                        <span class="value">{signal.strategy_id}</span>
                    </div>
                    <div class="row">
                        <span class="label">Symbol</span>
                        <span class="value">{signal.symbol}</span>
                    </div>
                    <div class="row">
                        <span class="label">Exchange</span>
                        <span class="value">{signal.exchange}</span>
                    </div>
                    <div class="row">
                        <span class="label">Timeframe</span>
                        <span class="value">{signal.timeframe}</span>
                    </div>
                    <div class="row">
                        <span class="label">Price</span>
                        <span class="value">{signal.price:.8f}</span>
                    </div>
        """

        if signal.entry_price:
            html += f"""
                    <div class="row">
                        <span class="label">Entry Price</span>
                        <span class="value">{signal.entry_price:.8f}</span>
                    </div>
            """

        if signal.stop_loss:
            html += f"""
                    <div class="row">
                        <span class="label">Stop Loss</span>
                        <span class="value">{signal.stop_loss:.8f}</span>
                    </div>
            """

        if signal.take_profit:
            html += f"""
                    <div class="row">
                        <span class="label">Take Profit</span>
                        <span class="value">{signal.take_profit:.8f}</span>
                    </div>
            """

        if signal.quantity:
            html += f"""
                    <div class="row">
                        <span class="label">Quantity</span>
                        <span class="value">{signal.quantity:.8f}</span>
                    </div>
            """

        rr = signal.calculate_risk_reward()
        if rr:
            html += f"""
                    <div class="row">
                        <span class="label">Risk/Reward</span>
                        <span class="value">1:{rr:.2f}</span>
                    </div>
            """

        html += f"""
                    <div class="row">
                        <span class="label">Confidence</span>
                        <span class="value">{signal.confidence}%</span>
                    </div>
                </div>
                <div class="footer">
                    Generated: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def send(self, signal: Signal) -> bool:
        """Send signal via email"""
        if not self.should_send(signal):
            return False

        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.to_addresses]):
            print("Email configuration incomplete")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self._get_subject(signal)
            msg['From'] = self.from_address or self.smtp_user
            msg['To'] = ', '.join(self.to_addresses)

            # Plain text version
            text_part = MIMEText(signal.format_message(), 'plain')
            msg.attach(text_part)

            # HTML version
            html_part = MIMEText(self._build_html_body(signal), 'html')
            msg.attach(html_part)

            # Send email
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                if self.use_tls:
                    server.starttls()

            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_address or self.smtp_user, self.to_addresses, msg.as_string())
            server.quit()

            return True

        except smtplib.SMTPAuthenticationError:
            print("Email authentication failed. Check credentials.")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP error: {e}")
            return False
        except Exception as e:
            print(f"Email error: {e}")
            return False

    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                if self.use_tls:
                    server.starttls()

            server.login(self.smtp_user, self.smtp_password)
            server.quit()
            return True

        except Exception:
            return False
