import logging
import os
from datetime import datetime

def setup_logger(name="trading_bot", log_level=logging.INFO):
    """
    Set up logger with both file and console handlers
    One main log file with different levels as requested
    """
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Prevent duplicate logs if logger already exists
    if logger.hasHandlers():
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler - logs everything to main file
    log_filename = f"logs/trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler - only INFO and above for clean output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create default logger instance
logger = setup_logger()

# Convenience functions for different log types
def log_api_request(method, endpoint, params=None):
    """Log API requests for debugging"""
    logger.debug(f"API Request: {method} {endpoint} | Params: {params}")

def log_api_response(response_data, status_code=None):
    """Log API responses"""
    logger.debug(f"API Response: Status {status_code} | Data: {response_data}")

def log_trade(symbol, side, order_type, quantity, price=None, order_id=None):
    """Log trading operations"""
    price_info = f" @ {price}" if price else ""
    logger.info(f"TRADE: {side} {quantity} {symbol} {order_type}{price_info} | Order ID: {order_id}")

def log_error(error_msg, exception=None):
    """Log errors with optional exception details"""
    if exception:
        logger.error(f"ERROR: {error_msg} | Exception: {str(exception)}")
    else:
        logger.error(f"ERROR: {error_msg}")
