import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import time
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from bot.trading_bot import BasicBot
from utils.exceptions import (
    TradingBotError, 
    InvalidOrderError, 
    InsufficientBalanceError,
    ConnectionError
)

# Page configuration
st.set_page_config(
    page_title="Binance Trading Bot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'bot' not in st.session_state:
        st.session_state.bot = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None

def connect_bot():
    """Initialize and connect the trading bot"""
    try:
        with st.spinner("Connecting to Binance Testnet..."):
            bot = BasicBot(testnet=True)
            if bot.test_connection():
                st.session_state.bot = bot
                st.session_state.connected = True
                return True
            else:
                st.session_state.connected = False
                return False
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")
        st.session_state.connected = False
        return False

def disconnect_bot():
    """Disconnect the trading bot"""
    st.session_state.bot = None
    st.session_state.connected = False

def format_currency(value, decimals=8):
    """Format currency values"""
    try:
        return f"{float(value):.{decimals}f}".rstrip('0').rstrip('.')
    except:
        return str(value)

def display_sidebar():
    """Display sidebar with connection and settings"""
    st.sidebar.title("⚙️ Bot Control")
    
    # Connection status - FIXED LAYOUT
    if st.session_state.connected:
        st.sidebar.success("✅ Connected to Testnet")
        if st.sidebar.button("🔌 Disconnect", type="secondary", use_container_width=True):
            disconnect_bot()
            st.rerun()
    else:
        st.sidebar.error("❌ Not Connected")
        if st.sidebar.button("🔗 Connect to Testnet", type="primary", use_container_width=True):
            if connect_bot():
                st.success("Connected successfully!")
                st.rerun()
            else:
                st.error("Connection failed!")
    
    st.sidebar.markdown("---")
    
    # FIXED: Refresh controls with proper alignment
    st.sidebar.subheader("🔄 Data Refresh")
    
    if st.sidebar.button("🔄 Refresh Now", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    if st.session_state.last_refresh:
        st.sidebar.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    st.sidebar.markdown("---")
    
    # Settings
    st.sidebar.subheader("⚙️ Settings")
    st.sidebar.selectbox("Default Symbol", ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT"], key="default_symbol")
    st.sidebar.number_input("Default Quantity", min_value=0.001, value=0.001, step=0.001, key="default_quantity")

def display_account_balance():
    """Display account balance information"""
    if not st.session_state.connected:
        st.warning("Connect to view account balance")
        return
    
    try:
        balance_data = st.session_state.bot.get_account_balance()
        
        st.subheader("💰 Account Balance")
        
        # Filter non-zero balances
        active_balances = [b for b in balance_data if float(b.get('balance', 0)) > 0]
        
        if not active_balances:
            st.info("No active balances found")
            return
        
        # Display in columns
        cols = st.columns(min(len(active_balances), 4))
        for i, asset in enumerate(active_balances):
            with cols[i % 4]:
                balance = float(asset.get('balance', 0))
                st.metric(
                    label=asset.get('asset', 'Unknown'),
                    value=format_currency(balance, 4)
                )
        
        # FIXED: Detailed table - Handle different balance structures safely
        with st.expander("📊 Detailed Balance"):
            # Create clean DataFrame with only guaranteed fields
            clean_data = []
            for item in active_balances:
                row = {
                    'Asset': item.get('asset', 'Unknown'),
                    'Balance': float(item.get('balance', 0))
                }
                # Add optional fields if they exist
                if 'crossWalletBalance' in item:
                    row['Cross Wallet'] = float(item.get('crossWalletBalance', 0))
                if 'withdrawAvailable' in item:
                    row['Available'] = float(item.get('withdrawAvailable', 0))
                if 'walletBalance' in item:
                    row['Wallet Balance'] = float(item.get('walletBalance', 0))
                
                clean_data.append(row)
            
            df = pd.DataFrame(clean_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"Failed to get balance: {str(e)}")

def display_order_form():
    """Display order placement form"""
    if not st.session_state.connected:
        st.warning("Connect to place orders")
        return
    
    st.subheader("📈 Place Order")
    
    with st.form("order_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            symbol = st.text_input("Symbol", value=st.session_state.get('default_symbol', 'BTCUSDT'))
            side = st.selectbox("Side", ["BUY", "SELL"])
        
        with col2:
            order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
            quantity = st.number_input("Quantity", 
                                     min_value=0.001, 
                                     value=st.session_state.get('default_quantity', 0.001),
                                     step=0.001, 
                                     format="%.6f")
        
        with col3:
            if order_type == "LIMIT":
                # Get current price for reference
                try:
                    current_price = st.session_state.bot.get_current_price(symbol)
                    st.info(f"Current Price: ${current_price:,.2f}")
                    price = st.number_input("Price", 
                                          min_value=0.01,
                                          value=float(current_price),
                                          step=0.01,
                                          format="%.2f")
                except:
                    price = st.number_input("Price", min_value=0.01, step=0.01, format="%.2f")
            else:
                price = None
                st.info("Market order - no price needed")
        
        # Order summary
        st.markdown("---")
        summary_col1, summary_col2 = st.columns(2)
        with summary_col1:
            st.write("**Order Summary:**")
            st.write(f"• Symbol: {symbol}")
            st.write(f"• Side: {side}")
            st.write(f"• Type: {order_type}")
            st.write(f"• Quantity: {quantity}")
            if price:
                st.write(f"• Price: ${price:,.2f}")
        
        with summary_col2:
            if price and quantity:
                total_value = price * quantity
                st.write("**Estimated Total:**")
                st.write(f"${total_value:,.2f}")
        
        # Submit button - FIXED alignment
        submitted = st.form_submit_button(
            "🚀 Place Order", 
            type="primary", 
            use_container_width=True
        )
        
        if submitted:
            try:
                with st.spinner("Placing order..."):
                    if order_type == "MARKET":
                        result = st.session_state.bot.place_market_order(symbol, side, quantity)
                    else:
                        result = st.session_state.bot.place_limit_order(symbol, side, quantity, price)
                
                st.success("✅ Order placed successfully!")
                
                # Display order details
                with st.expander("📋 Order Details", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Order ID:** {result.get('orderId')}")
                        st.write(f"**Symbol:** {result.get('symbol')}")
                        st.write(f"**Side:** {result.get('side')}")
                        st.write(f"**Type:** {result.get('type')}")
                    with col2:
                        st.write(f"**Quantity:** {result.get('origQty', result.get('quantity'))}")
                        st.write(f"**Status:** {result.get('status')}")
                        if result.get('price') and result.get('price') != '0':
                            st.write(f"**Price:** ${float(result.get('price')):,.2f}")
                
            except InvalidOrderError as e:
                st.error(f"❌ Invalid Order: {str(e)}")
            except InsufficientBalanceError as e:
                st.error(f"❌ Insufficient Balance: {str(e)}")
            except Exception as e:
                st.error(f"❌ Order Failed: {str(e)}")

def display_open_orders():
    """Display open orders"""
    if not st.session_state.connected:
        st.warning("Connect to view open orders")
        return
    
    st.subheader("📋 Open Orders")
    
    # FIXED: Better filter layout
    col1, col2 = st.columns([4, 1])
    with col1:
        filter_symbol = st.text_input("Filter by Symbol (optional)", placeholder="e.g., BTCUSDT")
    with col2:
        st.write("")  # Spacer for alignment
        refresh_orders = st.button("🔄 Refresh", use_container_width=True)
    
    try:
        orders = st.session_state.bot.get_open_orders(filter_symbol if filter_symbol else None)
        
        if not orders:
            st.info("No open orders found")
            return
        
        # FIXED: Better DataFrame processing - prevents glitches
        df = pd.DataFrame(orders)
        
        # Ensure proper column selection and formatting
        essential_columns = ['orderId', 'symbol', 'side', 'type', 'origQty', 'price', 'status']
        available_columns = [col for col in essential_columns if col in df.columns]
        
        # Add time column if available
        if 'updateTime' in df.columns:
            try:
                df['time'] = pd.to_datetime(df['updateTime'], unit='ms').dt.strftime('%H:%M:%S')
                available_columns.append('time')
            except:
                pass
        
        # Create clean display DataFrame
        display_df = df[available_columns].copy()
        
        # FIXED: Better price formatting to prevent glitches
        if 'price' in display_df.columns:
            display_df['price'] = display_df['price'].apply(
                lambda x: 'MARKET' if str(x) == '0' or str(x) == '0.0' else f"${float(x):,.2f}"
            )
        
        # Clean column names for better display
        column_mapping = {
            'orderId': 'Order ID',
            'symbol': 'Symbol', 
            'side': 'Side',
            'type': 'Type',
            'origQty': 'Quantity',
            'price': 'Price',
            'status': 'Status',
            'time': 'Time'
        }
        
        display_df = display_df.rename(columns=column_mapping)
        
        # FIXED: Better table display with configuration
        st.dataframe(
            display_df, 
            use_container_width=True,
            hide_index=True,
            height=300
        )
        
        # FIXED: Better order management layout
        st.markdown("---")
        st.subheader("🗑️ Cancel Order")
        
        # Use original df for cancel operations (not display_df)
        cancel_col1, cancel_col2, cancel_col3 = st.columns([2, 3, 1])
        
        with cancel_col1:
            cancel_symbol = st.selectbox("Symbol", df['symbol'].unique(), key="cancel_symbol")
        
        with cancel_col2:
            # Filter orders by selected symbol
            symbol_orders = df[df['symbol'] == cancel_symbol]
            if not symbol_orders.empty:
                order_options = []
                for _, row in symbol_orders.iterrows():
                    order_id = row['orderId']
                    side = row['side']
                    qty = row['origQty']
                    order_options.append(f"{order_id} ({side} {qty})")
                
                selected_order = st.selectbox("Order", order_options, key="cancel_order")
                # Extract order ID from selection
                cancel_order_id = int(selected_order.split(' ')[0]) if selected_order else None
            else:
                st.info("No orders for selected symbol")
                cancel_order_id = None
        
        with cancel_col3:
            st.write("")  # Spacer for alignment
            if cancel_order_id and st.button("❌ Cancel", type="secondary", use_container_width=True):
                try:
                    st.session_state.bot.cancel_order(cancel_symbol, cancel_order_id)
                    st.success(f"Order {cancel_order_id} cancelled!")
                    time.sleep(1)  # Brief pause before refresh
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to cancel: {str(e)}")
                    
    except Exception as e:
        st.error(f"Failed to get orders: {str(e)}")

def display_price_checker():
    """Display price checking tool"""
    if not st.session_state.connected:
        st.warning("Connect to check prices")
        return
    
    st.subheader("💲 Price Checker")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        price_symbol = st.text_input("Enter Symbol", value="BTCUSDT", key="price_symbol")
    with col2:
        st.write("")  # Spacer for alignment
        check_price = st.button("📊 Get Price", type="primary", use_container_width=True)
    
    if check_price or price_symbol:
        try:
            current_price = st.session_state.bot.get_current_price(price_symbol)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${current_price:,.2f}")
            
            # Additional symbol info
            with st.expander(f"📈 {price_symbol} Details"):
                try:
                    symbol_info = st.session_state.bot.get_symbol_info(price_symbol)
                    info_df = pd.DataFrame([{
                        'Symbol': symbol_info.get('symbol'),
                        'Status': symbol_info.get('status'),
                        'Base Asset': symbol_info.get('baseAsset'),
                        'Quote Asset': symbol_info.get('quoteAsset'),
                    }])
                    st.dataframe(info_df, use_container_width=True, hide_index=True)
                except:
                    st.info("Additional symbol information not available")
                    
        except Exception as e:
            st.error(f"Failed to get price: {str(e)}")

def main():
    """Main Streamlit application"""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🚀 Binance Futures Trading Bot</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Testnet Trading Interface</p>', unsafe_allow_html=True)
    
    # Sidebar
    display_sidebar()
    
    # Main content
    if not st.session_state.connected:
        st.warning("⚠️ Please connect to Binance Testnet using the sidebar to start trading")
        return
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Dashboard", "📈 Trade", "📋 Orders", "💲 Prices"])
    
    with tab1:
        display_account_balance()
        
        # Quick stats
        st.markdown("---")
        try:
            orders = st.session_state.bot.get_open_orders()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Open Orders", len(orders))
            with col2:
                st.metric("Bot Status", "🟢 Active")
            with col3:
                st.metric("Connection", "🌐 Testnet")
        except:
            pass
    
    with tab2:
        display_order_form()
    
    with tab3:
        display_open_orders()
    
    with tab4:
        display_price_checker()
    
    # Footer
    st.markdown("---")
    st.caption("⚠️ This is a testnet trading bot. No real money is involved.")

if __name__ == "__main__":
    main()
