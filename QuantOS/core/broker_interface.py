"""
QuantOS™ v7.0.0 - Abstract Broker Interface
Copyright (c) 2026 Cemini23 / Claudio Barone Jr.
"""
from abc import ABC, abstractmethod

class BrokerInterface(ABC):
    @abstractmethod
    def authenticate(self):
        """Authenticates with the broker API."""
        pass

    @abstractmethod
    def get_buying_power(self) -> float:
        """Returns the current available cash for trading."""
        pass

    @abstractmethod
    def get_positions(self) -> list:
        """Returns a list of current open positions."""
        pass

    @abstractmethod
    def get_latest_price(self, symbol: str) -> float:
        """Returns the current market price for a symbol."""
        pass

    @abstractmethod
    def submit_order(self, symbol: str, amount: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        """Submits a buy/sell order based on dollar amount."""
        pass

    @abstractmethod
    def submit_order_by_quantity(self, symbol: str, qty: float, side: str, order_type: str = "market", limit_price: float = None) -> dict:
        """Submits a buy/sell order based on share quantity."""
        pass

    @abstractmethod
    def cancel_all_orders(self):
        """Cancels all pending orders."""
        pass
