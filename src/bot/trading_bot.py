"""
BasicBot - Binance Futures Testnet helper

This module implements BasicBot which wraps Binance Python SDK calls
for a simple trading workflow (market/limit orders, balances, open orders, cancellation).
Only logging, validation and retry decorators are applied — core logic is thin.

CLI usage examples (run from project root in PowerShell):
cd "c:\Users\LENOVO\OneDrive\Desktop\Trading bot"

# Place market buy order
python src\ui\cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Place limit sell order
python src\ui\cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 45000

# Check account balance
python src\ui\cli.py --balance

# View open orders (optionally filter by symbol)
python src\ui\cli.py --orders
python src\ui\cli.py --orders --symbol BTCUSDT

# Cancel order
python src\ui\cli.py --cancel --symbol BTCUSDT --order-id 12345

# Get current price
python src\ui\cli.py --price-check --symbol BTCUSDT
"""

from binance.client import Client
import os
from dotenv import load_dotenv
from utils.logger import logger, log_trade, log_api_request, log_error
from utils.exceptions import (
    retry_api_call, 
    validate_trading_params,
    InsufficientBalanceError, 
    InvalidOrderError, 
    OrderPlacementError,
    OrderCancellationError,
    ConnectionError,
    TradingBotError
)

# Load environment variables from .env
load_dotenv()

class BasicBot:
    """
    Basic Trading Bot for Binance Futures Testnet

    This class provides small, well-documented helpers:
    - test_connection: verify API connectivity and permissions
    - get_account_balance: fetch futures account balances
    - place_market_order: submit a market order (BUY/SELL)
    - place_limit_order: submit a limit order with price and GTC
    - get_open_orders: list open orders (optional symbol filter)
    - cancel_order: cancel a specific order by symbol and order id
    - get_symbol_info: retrieve exchange metadata for a symbol
    - get_current_price: get latest ticker price for a symbol

    All network methods are decorated with retry_api_call to reduce transient failures.
    """
    
    def __init__(self, api_key=None, api_secret=None, testnet=True):
        """Initialize the trading bot with API credentials.

        Raises:
            ValueError: if API credentials are missing.
            ConnectionError: if Binance client initialization fails.
        """
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_API_SECRET')
        self.testnet = testnet
        
        if not self.api_key or not self.api_secret:
            raise ValueError("API credentials not found. Check your .env file.")
        
        # Initialize Binance client
        try:
            self.client = Client(
                self.api_key, 
                self.api_secret,
                testnet=self.testnet
            )
            logger.info("BasicBot initialized successfully")
        except Exception as e:
            log_error("Failed to initialize bot", e)
            raise ConnectionError(f"Bot initialization failed: {str(e)}")
    
    @retry_api_call(max_retries=3, delay=1)
    def test_connection(self):
        """Test connection to Binance.

        Performs a minimal set of API calls (server time + account fetch)
        to ensure the API key/secret are valid and permissions are correct.

        Returns:
            bool: True when reachable and account info accessible, False otherwise.
        """
        try:
            log_api_request("GET", "server_time")
            server_time = self.client.get_server_time()
            
            log_api_request("GET", "futures_account")
            account_info = self.client.futures_account()
            
            logger.info("Connection test successful")
            return True
        except Exception as e:
            log_error("Connection test failed", e)
            return False
    
    @retry_api_call(max_retries=3, delay=1)
    def get_account_balance(self):
        """Get futures account balance.

        Returns:
            list: Raw balance entries from Binance futures_account_balance.
        Raises:
            Exception: Propagates underlying client errors.
        """
        try:
            log_api_request("GET", "futures_account_balance")
            balance = self.client.futures_account_balance()
            logger.info("Account balance retrieved successfully")
            return balance
        except Exception as e:
            log_error("Failed to get account balance", e)
            raise
    
    @retry_api_call(max_retries=3, delay=1)
    def place_market_order(self, symbol, side, quantity):
        """
        Place a market order.

        Args:
            symbol (str): Trading pair (e.g., 'BTCUSDT')
            side (str): 'BUY' or 'SELL'
            quantity (float): Order quantity

        Returns:
            dict: Order response from Binance

        Raises:
            InvalidOrderError: if validation fails.
            Exception: for underlying client errors (logged).
        """
        # Validate parameters
        validate_trading_params(symbol=symbol, side=side, quantity=quantity, order_type='MARKET')
        
        symbol = symbol.upper()
        side = side.upper()
        
        try:
            log_api_request("POST", "futures_create_order", {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': quantity
            })
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            # Log successful trade
            log_trade(
                symbol=symbol,
                side=side,
                order_type='MARKET',
                quantity=quantity,
                order_id=order.get('orderId')
            )
            
            logger.info(f"Market order placed successfully: Order ID {order.get('orderId')}")
            return order
            
        except Exception as e:
            log_error(f"Failed to place market order: {symbol} {side} {quantity}", e)
            raise
    
    @retry_api_call(max_retries=3, delay=1)
    def place_limit_order(self, symbol, side, quantity, price):
        """
        Place a limit order.

        Args:
            symbol (str): Trading pair (e.g., 'BTCUSDT')
            side (str): 'BUY' or 'SELL'  
            quantity (float): Order quantity
            price (float): Order price

        Returns:
            dict: Order response from Binance

        Raises:
            InvalidOrderError: on invalid params
            Exception: for underlying client errors (logged)
        """
        # Validate parameters
        validate_trading_params(symbol=symbol, side=side, quantity=quantity, 
                              price=price, order_type='LIMIT')
        
        symbol = symbol.upper()
        side = side.upper()
        
        try:
            log_api_request("POST", "futures_create_order", {
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT',
                'timeInForce': 'GTC',
                'quantity': quantity,
                'price': price
            })
            
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            
            # Log successful trade
            log_trade(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                order_id=order.get('orderId')
            )
            
            logger.info(f"Limit order placed successfully: Order ID {order.get('orderId')}")
            return order
            
        except Exception as e:
            log_error(f"Failed to place limit order: {symbol} {side} {quantity} @ {price}", e)
            raise
    
    @retry_api_call(max_retries=3, delay=1)
    def get_open_orders(self, symbol=None):
        """
        Get open orders.

        Args:
            symbol (str, optional): Trading pair to filter orders

        Returns:
            list: List of open orders

        Raises:
            Exception: for underlying client errors (logged)
        """
        try:
            log_api_request("GET", "futures_get_open_orders", {'symbol': symbol})
            
            if symbol:
                validate_trading_params(symbol=symbol)
                orders = self.client.futures_get_open_orders(symbol=symbol.upper())
            else:
                orders = self.client.futures_get_open_orders()
            
            logger.info(f"Retrieved {len(orders)} open orders")
            return orders
            
        except Exception as e:
            log_error("Failed to get open orders", e)
            raise
    
    @retry_api_call(max_retries=3, delay=1)
    def cancel_order(self, symbol, order_id):
        """
        Cancel an order.

        Args:
            symbol (str): Trading pair
            order_id (int): Order ID to cancel

        Returns:
            dict: Cancellation response

        Raises:
            InvalidOrderError: if symbol or order_id missing
            OrderCancellationError: wrapped when cancellation fails
        """
        if not symbol or not order_id:
            raise InvalidOrderError("Symbol and order_id are required")
        
        validate_trading_params(symbol=symbol)
        
        try:
            log_api_request("DELETE", "futures_cancel_order", {
                'symbol': symbol.upper(),
                'orderId': order_id
            })
            
            result = self.client.futures_cancel_order(
                symbol=symbol.upper(), 
                orderId=order_id
            )
            
            logger.info(f"Order {order_id} cancelled successfully")
            return result
            
        except Exception as e:
            log_error(f"Failed to cancel order {order_id}", e)
            raise OrderCancellationError(f"Failed to cancel order {order_id}: {str(e)}", 
                                    order_id=order_id, symbol=symbol)

    @retry_api_call(max_retries=3, delay=1)
    def get_symbol_info(self, symbol):
        """
        Get trading symbol information (for precision, min quantity, etc.)

        Args:
            symbol (str): Trading pair

        Returns:
            dict: Symbol information

        Raises:
            InvalidOrderError: if symbol not found
            Exception: for underlying client errors (logged)
        """
        validate_trading_params(symbol=symbol)
        
        try:
            log_api_request("GET", "futures_exchange_info")
            exchange_info = self.client.futures_exchange_info()
            
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol.upper():
                    logger.info(f"Symbol info retrieved for {symbol}")
                    return s
            
            raise InvalidOrderError(f"Symbol {symbol} not found")
            
        except Exception as e:
            log_error(f"Failed to get symbol info for {symbol}", e)
            raise

    def get_current_price(self, symbol):
        """
        Get current price for a symbol.

        Args:
            symbol (str): Trading pair

        Returns:
            float: Current price

        Raises:
            Exception: for underlying client errors (logged)
        """
        validate_trading_params(symbol=symbol)
        
        try:
            log_api_request("GET", "futures_symbol_ticker", {'symbol': symbol})
            ticker = self.client.futures_symbol_ticker(symbol=symbol.upper())
            price = float(ticker['price'])
            logger.info(f"Current price for {symbol}: {price}")
            return price
            
        except Exception as e:
            log_error(f"Failed to get current price for {symbol}", e)
            raise
