import time
import functools
from binance.exceptions import BinanceAPIException, BinanceOrderException
from utils.logger import logger

# ========================================
# Custom Exception Classes for Trading Bot
# ========================================

class TradingBotError(Exception):
    """Base exception for all trading bot errors"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

class ConnectionError(TradingBotError):
    """Raised when connection to exchange fails"""
    def __init__(self, message="Connection to exchange failed", **kwargs):
        super().__init__(message, **kwargs)

class InsufficientBalanceError(TradingBotError):
    """Raised when account has insufficient balance for trade"""
    def __init__(self, message="Insufficient balance", required_balance=None, available_balance=None, **kwargs):
        self.required_balance = required_balance
        self.available_balance = available_balance
        details = kwargs.get('details', {})
        if required_balance and available_balance:
            details.update({
                'required': required_balance,
                'available': available_balance
            })
        super().__init__(message, details=details, **kwargs)

class InvalidOrderError(TradingBotError):
    """Raised when order parameters are invalid"""
    def __init__(self, message="Invalid order parameters", field=None, value=None, **kwargs):
        self.field = field
        self.value = value
        details = kwargs.get('details', {})
        if field:
            details.update({'invalid_field': field, 'invalid_value': value})
        super().__init__(message, details=details, **kwargs)

class OrderPlacementError(TradingBotError):
    """Raised when order placement fails"""
    def __init__(self, message="Order placement failed", order_details=None, **kwargs):
        self.order_details = order_details or {}
        details = kwargs.get('details', {})
        details.update(self.order_details)
        super().__init__(message, details=details, **kwargs)

class OrderCancellationError(TradingBotError):
    """Raised when order cancellation fails"""
    def __init__(self, message="Order cancellation failed", order_id=None, symbol=None, **kwargs):
        self.order_id = order_id
        self.symbol = symbol
        details = kwargs.get('details', {})
        if order_id:
            details.update({'order_id': order_id, 'symbol': symbol})
        super().__init__(message, details=details, **kwargs)

class RateLimitError(TradingBotError):
    """Raised when API rate limit is exceeded"""
    def __init__(self, message="Rate limit exceeded", retry_after=None, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)

class MarketDataError(TradingBotError):
    """Raised when market data is unavailable or invalid"""
    def __init__(self, message="Market data error", symbol=None, **kwargs):
        self.symbol = symbol
        super().__init__(message, **kwargs)

class PrecisionError(TradingBotError):
    """Raised when order precision is invalid"""
    def __init__(self, message="Precision error", symbol=None, field=None, value=None, **kwargs):
        self.symbol = symbol
        self.field = field
        self.value = value
        super().__init__(message, **kwargs)

class SymbolError(TradingBotError):
    """Raised when trading symbol is invalid or unavailable"""
    def __init__(self, message="Symbol error", symbol=None, **kwargs):
        self.symbol = symbol
        super().__init__(message, **kwargs)

# ========================================
# Binance Error Code Mapping
# ========================================

BINANCE_ERROR_MAP = {
    # Connection and Server Issues (1000-1099)
    -1000: (TradingBotError, "Unknown error occurred"),
    -1001: (ConnectionError, "Internal error; unable to process request"),
    -1002: (ConnectionError, "Unauthorized request"),
    -1003: (RateLimitError, "Too many requests"),
    -1006: (TradingBotError, "Unexpected response received"),
    -1007: (ConnectionError, "Request timeout"),
    -1008: (RateLimitError, "Server overloaded"),
    -1014: (TradingBotError, "Unsupported order combination"),
    -1015: (RateLimitError, "Too many orders"),
    -1016: (TradingBotError, "Service shutting down"),
    -1020: (TradingBotError, "Unsupported operation"),
    -1021: (ConnectionError, "Timestamp outside recv window"),
    -1022: (ConnectionError, "Invalid signature"),
    
    # Request Parameter Issues (1100-1199)
    -1100: (InvalidOrderError, "Illegal characters found in parameter"),
    -1101: (InvalidOrderError, "Too many parameters sent"),
    -1102: (InvalidOrderError, "Mandatory parameter was not sent"),
    -1103: (InvalidOrderError, "Unknown parameter was sent"),
    -1104: (InvalidOrderError, "Not all parameters were read"),
    -1105: (InvalidOrderError, "Parameter was empty"),
    -1106: (InvalidOrderError, "Parameter was not required"),
    -1111: (PrecisionError, "Precision is over the maximum defined"),
    -1112: (MarketDataError, "No orders on book for symbol"),
    -1114: (InvalidOrderError, "TimeInForce parameter sent when not required"),
    -1115: (InvalidOrderError, "Invalid timeInForce"),
    -1116: (InvalidOrderError, "Invalid orderType"),
    -1117: (InvalidOrderError, "Invalid side"),
    -1118: (InvalidOrderError, "New client order ID was empty"),
    -1119: (InvalidOrderError, "Original client order ID was empty"),
    -1120: (InvalidOrderError, "Invalid interval"),
    -1121: (SymbolError, "Invalid symbol"),
    -1125: (ConnectionError, "Invalid listen key"),
    -1127: (InvalidOrderError, "Lookup interval is too big"),
    -1128: (InvalidOrderError, "Combination of optional parameters invalid"),
    -1130: (InvalidOrderError, "Invalid data sent for parameter"),
    -1131: (InvalidOrderError, "recvWindow must be less than 60000"),
    
    # Order Issues (2000-2099)
    -2010: (InsufficientBalanceError, "Account has insufficient balance"),
    -2011: (OrderCancellationError, "Unknown order sent"),
    -2013: (OrderCancellationError, "Order does not exist"),
    -2014: (ConnectionError, "API-key format invalid"),
    -2015: (ConnectionError, "Invalid API-key, IP, or permissions"),
    -2016: (TradingBotError, "No trading window could be found"),
    -2018: (InsufficientBalanceError, "Balance is insufficient"),
    -2019: (InsufficientBalanceError, "Margin is insufficient"),
    -2020: (TradingBotError, "Unable to fill"),
    -2021: (OrderCancellationError, "Order would immediately trigger"),
    -2022: (InvalidOrderError, "ReduceOnly order is rejected"),
}

# ========================================
# Enhanced Retry Decorator
# ========================================

def retry_api_call(max_retries=3, delay=1, backoff=2, exceptions=None):
    """
    Enhanced decorator to retry API calls with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch (default: all exceptions)
    """
    if exceptions is None:
        exceptions = (Exception,)
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            last_exception = None
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                
                except BinanceAPIException as e:
                    last_exception = e
                    # Map Binance error to custom exception
                    exception_class, default_message = BINANCE_ERROR_MAP.get(
                        e.code, (TradingBotError, f"Binance API Error {e.code}")
                    )
                    
                    # Special handling for rate limits
                    if e.code == -1003:
                        retry_after = int(e.response.headers.get('Retry-After', current_delay))
                        current_delay = max(current_delay, retry_after)
                        logger.warning(f"Rate limit hit, retrying in {current_delay}s... ({retries + 1}/{max_retries})")
                    elif e.code == -1021:  # Timestamp error
                        logger.warning(f"Timestamp error, retrying... ({retries + 1}/{max_retries})")
                    elif e.code in [-2010, -2018]:  # Insufficient balance - don't retry
                        raise InsufficientBalanceError(e.message, error_code=e.code)
                    elif e.code in [-1111, -1115, -1116, -1117, -1121]:  # Parameter errors - don't retry
                        raise exception_class(e.message, error_code=e.code)
                    else:
                        logger.error(f"Binance API Error {e.code}: {e.message}")
                        if retries == max_retries - 1:
                            raise exception_class(e.message, error_code=e.code)
                
                except BinanceOrderException as e:
                    last_exception = e
                    logger.error(f"Binance Order Error: {e.message}")
                    # Order exceptions usually shouldn't be retried
                    raise OrderPlacementError(f"Order failed: {e.message}")
                
                except exceptions as e:
                    last_exception = e
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                    if retries == max_retries - 1:
                        if isinstance(e, TradingBotError):
                            raise
                        else:
                            raise ConnectionError(f"Connection failed after {max_retries} retries: {str(e)}")
                
                retries += 1
                if retries < max_retries:
                    logger.info(f"Retrying in {current_delay} seconds... (attempt {retries + 1}/{max_retries})")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # If we get here, all retries failed
            if last_exception:
                if isinstance(last_exception, BinanceAPIException):
                    exception_class, _ = BINANCE_ERROR_MAP.get(
                        last_exception.code, (TradingBotError, "Unknown error")
                    )
                    raise exception_class(f"Max retries exceeded: {last_exception.message}", 
                                        error_code=last_exception.code)
                else:
                    raise ConnectionError(f"Max retries ({max_retries}) exceeded: {str(last_exception)}")
            else:
                raise ConnectionError(f"Max retries ({max_retries}) exceeded")
        
        return wrapper
    return decorator

# ========================================
# Utility Functions
# ========================================

def handle_binance_error(error):
    """Convert Binance errors to custom exceptions with proper mapping"""
    if isinstance(error, BinanceAPIException):
        exception_class, default_message = BINANCE_ERROR_MAP.get(
            error.code, (TradingBotError, f"Unknown Binance API error {error.code}")
        )
        raise exception_class(error.message, error_code=error.code)
    elif isinstance(error, BinanceOrderException):
        raise OrderPlacementError(f"Order error: {error.message}")
    else:
        raise TradingBotError(f"Unexpected error: {str(error)}")

def validate_trading_params(symbol=None, side=None, quantity=None, price=None, order_type=None):
    """Validate common trading parameters and raise appropriate exceptions"""
    if symbol is not None:
        if not isinstance(symbol, str) or not symbol.strip():
            raise InvalidOrderError("Symbol must be a non-empty string", field="symbol", value=symbol)
    
    if side is not None:
        if side.upper() not in ['BUY', 'SELL']:
            raise InvalidOrderError("Side must be 'BUY' or 'SELL'", field="side", value=side)
    
    if quantity is not None:
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            raise InvalidOrderError("Quantity must be a positive number", field="quantity", value=quantity)
    
    if price is not None:
        if not isinstance(price, (int, float)) or price <= 0:
            raise InvalidOrderError("Price must be a positive number", field="price", value=price)
    
    if order_type is not None:
        valid_types = ['MARKET', 'LIMIT', 'STOP', 'TAKE_PROFIT', 'STOP_MARKET', 'TAKE_PROFIT_MARKET']
        if order_type.upper() not in valid_types:
            raise InvalidOrderError(f"Order type must be one of {valid_types}", 
                                field="order_type", value=order_type)
