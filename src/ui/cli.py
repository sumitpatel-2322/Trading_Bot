"""
Command Line Interface for Binance Trading Bot
Supports market/limit orders, balance checking, and order management
"""

import argparse
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from bot.trading_bot import BasicBot
from utils.logger import logger
from utils.exceptions import (
    TradingBotError, 
    InvalidOrderError,
    InsufficientBalanceError,
    ConnectionError
)

class TradingCLI:
    """Command Line Interface for the Trading Bot"""
    
    def __init__(self):
        self.bot = None
    
    def initialize_bot(self):
        """Initialize the trading bot"""
        try:
            self.bot = BasicBot(testnet=True)
            if not self.bot.test_connection():
                print("❌ Failed to connect to Binance Testnet")
                return False
            print("✅ Connected to Binance Testnet successfully")
            return True
        except Exception as e:
            print(f"❌ Bot initialization failed: {str(e)}")
            return False
    
    def format_order_output(self, order):
        """Format order response for display"""
        print("\n" + "="*50)
        print("📋 ORDER EXECUTED SUCCESSFULLY")
        print("="*50)
        print(f"Order ID     : {order.get('orderId')}")
        print(f"Symbol       : {order.get('symbol')}")
        print(f"Side         : {order.get('side')}")
        print(f"Type         : {order.get('type')}")
        print(f"Quantity     : {order.get('origQty', order.get('quantity'))}")
        if order.get('price') and order.get('price') != '0':
            print(f"Price        : {order.get('price')}")
        print(f"Status       : {order.get('status')}")
        print(f"Time         : {order.get('updateTime', order.get('transactTime'))}")
        print("="*50)
    
    def format_balance_output(self, balance):
        """Format balance response for display"""
        print("\n" + "="*50)
        print("💰 ACCOUNT BALANCE")
        print("="*50)
        
        # Filter and display non-zero balances
        active_balances = [b for b in balance if float(b['balance']) > 0]
        
        if not active_balances:
            print("No balances found")
            return
        
        for asset in active_balances:
            print(f"{asset['asset']:<10} : {float(asset['balance']):.8f}")
        print("="*50)
    
    def format_orders_output(self, orders):
        """Format open orders for display"""
        print("\n" + "="*50)
        print("📋 OPEN ORDERS")
        print("="*50)
        
        if not orders:
            print("No open orders found")
            return
        
        print(f"{'Order ID':<12} {'Symbol':<12} {'Side':<4} {'Type':<6} {'Quantity':<12} {'Price':<12} {'Status'}")
        print("-" * 80)
        
        for order in orders:
            price = order.get('price', '0')
            if price == '0':
                price = 'MARKET'
            
            print(f"{order.get('orderId', ''):<12} "
                f"{order.get('symbol', ''):<12} "
                f"{order.get('side', ''):<4} "
                f"{order.get('type', ''):<6} "
                f"{order.get('origQty', ''):<12} "
                f"{price:<12} "
                f"{order.get('status', '')}")
        print("="*50)
    
    def handle_place_order(self, args):
        """Handle order placement"""
        try:
            if args.type.upper() == 'MARKET':
                order = self.bot.place_market_order(args.symbol, args.side, args.quantity)
            elif args.type.upper() == 'LIMIT':
                if not args.price:
                    print("❌ Error: Price is required for LIMIT orders")
                    return False
                order = self.bot.place_limit_order(args.symbol, args.side, args.quantity, args.price)
            else:
                print("❌ Error: Order type must be MARKET or LIMIT")
                return False
            
            self.format_order_output(order)
            return True
            
        except InvalidOrderError as e:
            print(f"❌ Invalid Order: {str(e)}")
            return False
        except InsufficientBalanceError as e:
            print(f"❌ Insufficient Balance: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Order Failed: {str(e)}")
            return False
    
    def handle_balance(self):
        """Handle balance display"""
        try:
            balance = self.bot.get_account_balance()
            self.format_balance_output(balance)
            return True
        except Exception as e:
            print(f"❌ Failed to get balance: {str(e)}")
            return False
    
    def handle_orders(self, symbol=None):
        """Handle open orders display"""
        try:
            orders = self.bot.get_open_orders(symbol)
            self.format_orders_output(orders)
            return True
        except Exception as e:
            print(f"❌ Failed to get orders: {str(e)}")
            return False
    
    def handle_cancel(self, symbol, order_id):
        """Handle order cancellation"""
        try:
            result = self.bot.cancel_order(symbol, order_id)
            print(f"✅ Order {order_id} cancelled successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to cancel order: {str(e)}")
            return False
    
    def handle_price(self, symbol):
        """Handle current price display"""
        try:
            price = self.bot.get_current_price(symbol)
            print(f"\n💲 Current Price for {symbol.upper()}: {price}")
            return True
        except Exception as e:
            print(f"❌ Failed to get price: {str(e)}")
            return False

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Binance Futures Trading Bot CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
# Place market buy order
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Place limit sell order  
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 45000

# Check account balance
python cli.py --balance

# View open orders
python cli.py --orders --symbol BTCUSDT

# Cancel order
python cli.py --cancel --symbol BTCUSDT --order-id 12345

# Get current price
python cli.py --price --symbol BTCUSDT
        """
    )
    
    # Trading parameters
    parser.add_argument('--symbol', type=str, help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('--side', choices=['BUY', 'SELL', 'buy', 'sell'], help='Order side')
    parser.add_argument('--type', choices=['MARKET', 'LIMIT', 'market', 'limit'], help='Order type')
    parser.add_argument('--quantity', type=float, help='Order quantity')
    parser.add_argument('--price', type=float, help='Order price (required for LIMIT orders)')
    
    # Actions
    parser.add_argument('--balance', action='store_true', help='Show account balance')
    parser.add_argument('--orders', action='store_true', help='Show open orders')
    parser.add_argument('--cancel', action='store_true', help='Cancel an order')
    parser.add_argument('--order-id', type=int, help='Order ID for cancellation')
    parser.add_argument('--price-check', action='store_true', help='Get current price')
    
    return parser

def validate_args(args):
    """Validate command line arguments"""
    # Check if any action is specified
    actions = [args.balance, args.orders, args.cancel, args.price_check]
    has_trading_params = args.symbol and args.side and args.type and args.quantity
    
    if not any(actions) and not has_trading_params:
        return False, "No valid action specified. Use --help for examples."
    
    # Validate trading order parameters
    if has_trading_params:
        if args.type.upper() == 'LIMIT' and not args.price:
            return False, "Price is required for LIMIT orders"
    
    # Validate cancel parameters
    if args.cancel:
        if not args.symbol or not args.order_id:
            return False, "Symbol and order-id are required for cancellation"
    
    # Validate price check parameters
    if args.price_check:
        if not args.symbol:
            return False, "Symbol is required for price check"
    
    return True, ""

def main():
    """Main CLI function"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate arguments
    valid, error_msg = validate_args(args)
    if not valid:
        print(f"❌ {error_msg}")
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI
    cli = TradingCLI()
    
    print("🚀 Binance Futures Trading Bot CLI")
    print("Initializing connection...")
    
    if not cli.initialize_bot():
        sys.exit(1)
    
    success = False
    
    try:
        # Handle different actions
        if args.balance:
            success = cli.handle_balance()
        
        elif args.orders:
            success = cli.handle_orders(args.symbol)
        
        elif args.cancel:
            success = cli.handle_cancel(args.symbol, args.order_id)
        
        elif args.price_check:
            success = cli.handle_price(args.symbol)
        
        elif args.symbol and args.side and args.type and args.quantity:
            success = cli.handle_place_order(args)
        
        else:
            print("❌ Invalid command combination")
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
