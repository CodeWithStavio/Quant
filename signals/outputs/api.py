"""
API Output Handler
==================
Send signals to REST API endpoints.
"""

import json
from typing import Optional, Dict, Any
from signals.base_output import BaseOutput
from signals.signal import Signal

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class APIOutput(BaseOutput):
    """
    REST API output handler for sending signals to external services.

    Features:
    - POST/PUT request methods
    - Custom headers and authentication
    - Retry logic
    - Timeout configuration
    """

    def __init__(
        self,
        name: str = "api",
        enabled: bool = True,
        endpoint: str = "http://localhost:8080/signals",
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
        timeout: int = 10,
        retries: int = 3,
        verify_ssl: bool = True
    ):
        """
        Initialize API output.

        Args:
            name: Handler name
            enabled: Whether handler is active
            endpoint: API endpoint URL
            method: HTTP method (POST or PUT)
            headers: Custom headers
            auth_token: Bearer token for authentication
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            verify_ssl: Verify SSL certificates
        """
        super().__init__(name, enabled)
        self.endpoint = endpoint
        self.method = method.upper()
        self.headers = headers or {}
        self.auth_token = auth_token
        self.timeout = timeout
        self.retries = retries
        self.verify_ssl = verify_ssl

        # Set default headers
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'

        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'

    def send(self, signal: Signal) -> bool:
        """Send signal to API endpoint"""
        if not self.should_send(signal):
            return False

        if not REQUESTS_AVAILABLE:
            print("API output requires 'requests' library. Install with: pip install requests")
            return False

        payload = signal.to_json()

        for attempt in range(self.retries):
            try:
                if self.method == "POST":
                    response = requests.post(
                        self.endpoint,
                        data=payload,
                        headers=self.headers,
                        timeout=self.timeout,
                        verify=self.verify_ssl
                    )
                elif self.method == "PUT":
                    response = requests.put(
                        self.endpoint,
                        data=payload,
                        headers=self.headers,
                        timeout=self.timeout,
                        verify=self.verify_ssl
                    )
                else:
                    print(f"Unsupported HTTP method: {self.method}")
                    return False

                if response.status_code in (200, 201, 202, 204):
                    return True
                else:
                    print(f"API request failed with status {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                print(f"API request timeout (attempt {attempt + 1}/{self.retries})")
            except requests.exceptions.ConnectionError:
                print(f"API connection error (attempt {attempt + 1}/{self.retries})")
            except Exception as e:
                print(f"API request error: {e}")
                return False

        return False

    def health_check(self) -> bool:
        """
        Check if API endpoint is reachable.

        Returns:
            True if endpoint responds, False otherwise
        """
        if not REQUESTS_AVAILABLE:
            return False

        try:
            response = requests.get(
                self.endpoint.rsplit('/', 1)[0],  # Base URL
                timeout=5,
                verify=self.verify_ssl
            )
            return response.status_code < 500
        except Exception:
            return False
