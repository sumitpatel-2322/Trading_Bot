#!/usr/bin/env python3
"""
Binance Trading Bot - Main Entry Point
Supports both CLI and Streamlit UI interfaces

Created for hiring task demonstration
"""

import sys
import argparse
import subprocess
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from src.bot.trading_bot import BasicBot
    from src.utils.logger import logger
    from src.utils.exceptions import TradingBotError, ConnectionError
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 BINANCE FUTURES TRADING BOT 🚀                    ║
║                                                              ║
║        Testnet Trading Bot for Hiring Task                  ║
║        Supports Market & Limit Orders                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def test_connection():
    """Test connection to Binance Testnet"""
    print("🔄 Testing connection to Binance Testnet...")
    
    try:
        bot = BasicBot(testnet=True)
        if bot.test_connection():
            # Get account info
            balance = bot.get_account_balance()
            usdt_balance = next((b for b in balance if b['asset'] == 'USDT'), None)
            
            print("✅ Connection successful!")
            print(f"📊 Account Status: Active")
            if usdt_balance:
                print(f"💰 USDT Balance: {float(usdt_balance['balance']):.2f}")
            print(f"🌐 Environment: Testnet")
            return True
        else:
            print("❌ Connection test failed")
            return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def launch_streamlit():
    """Launch Streamlit web interface"""
    print("🌐 Launching Streamlit Web Interface...")
    print("📍 URL: http://localhost:8501")
    print("⚠️  Press Ctrl+C to stop the server")
    
    streamlit_file = Path("src/ui/streamlit_app.py")
    
    if not streamlit_file.exists():
        print(f"❌ Streamlit app not found: {streamlit_file}")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(streamlit_file), 
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ])
        return True
    except KeyboardInterrupt:
        print("\n⚠️ Streamlit server stopped by user")
        return True
    except FileNotFoundError:
        print("❌ Streamlit not installed. Install with: pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ Failed to launch Streamlit: {str(e)}")
        return False

def launch_cli(cli_args):
    """Launch CLI interface with passed arguments"""
    print("⌨️  Launching Command Line Interface...")
    
    cli_file = Path("src/ui/cli.py")
    
    if not cli_file.exists():
        print(f"❌ CLI app not found: {cli_file}")
        return False
    
    try:
        # Pass all CLI arguments
        cmd = [sys.executable, str(cli_file)] + cli_args
        result = subprocess.run(cmd)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to launch CLI: {str(e)}")
        return False

def show_examples():
    """Show usage examples"""
    examples = """
📚 USAGE EXAMPLES:

🧪 Connection Testing:
   python main.py --test

🌐 Web Interface:
   python main.py --ui

⌨️  CLI Trading Examples:
   # Check balance
   python main.py --cli --balance
   
   # Place market buy order
   python main.py --cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
   
   # Place limit sell order
   python main.py --cli --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 45000
   
   # View open orders
   python main.py --cli --orders --symbol BTCUSDT
   
   # Cancel order
   python main.py --cli --cancel --symbol BTCUSDT --order-id 12345
   
   # Check current price
   python main.py --cli --price-check --symbol BTCUSDT

🔧 Direct CLI (Alternative):
   python src/ui/cli.py --help

📋 Requirements Met:
   ✅ Market and Limit Orders (BUY/SELL)
   ✅ Input validation and error handling
   ✅ API logging (requests/responses/errors)  
   ✅ Clean code structure for reusability
   ✅ Command-line interface
   ✅ Streamlit web interface (bonus)
   ✅ Testnet integration
"""
    print(examples)

def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Binance Futures Trading Bot - Main Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False  # We'll handle help manually
    )
    
    # Main interface options
    interface_group = parser.add_mutually_exclusive_group()
    interface_group.add_argument('--ui', action='store_true', 
                                help='Launch Streamlit web interface')
    interface_group.add_argument('--cli', action='store_true',
                                help='Launch command line interface')
    interface_group.add_argument('--test', action='store_true',
                                help='Test connection only')
    interface_group.add_argument('--examples', action='store_true',
                                help='Show usage examples')
    interface_group.add_argument('--help', '-h', action='store_true',
                                help='Show this help message')
    
    return parser

def main():
    """Main entry point"""
    print_banner()
    
    # Parse known args to separate main args from CLI args
    parser = create_parser()
    args, unknown_args = parser.parse_known_args()
    
    # Show help
    if args.help or (not args.ui and not args.cli and not args.test and not args.examples and not unknown_args):
        parser.print_help()
        show_examples()
        return
    
    # Show examples
    if args.examples:
        show_examples()
        return
    
    # Test connection
    if args.test:
        success = test_connection()
        sys.exit(0 if success else 1)
    
    # Check environment file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("📝 Make sure you have BINANCE_API_KEY and BINANCE_API_SECRET set")
        print()
    
    # Launch interfaces
    success = False
    
    if args.ui:
        # Test connection before launching UI
        if test_connection():
            print()
            success = launch_streamlit()
        else:
            print("❌ Cannot launch UI - connection test failed")
            sys.exit(1)
    
    elif args.cli:
        # Launch CLI with remaining arguments
        success = launch_cli(unknown_args)
    
    else:
        # If no specific interface chosen but have CLI args, use CLI
        if unknown_args:
            success = launch_cli(unknown_args)
        else:
            print("❌ No interface specified. Use --help for options.")
            sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Application interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
