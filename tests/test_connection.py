import os 
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

load_dotenv()
def test_connection():
    """Testing the connection to Binance Futures Testnet"""
    api_key=os.getenv('BINANCE_API_KEY')
    api_secret=os.getenv('BINANCE_API_SECRET')
    
    if not api_key:
        print("ERROR! Api credentials not found in .env file")
        return False
    try:
        client=Client(api_key,api_secret,testnet=True)
        print("Testing connection to Binance Futures Testnet...")
        server_time=client.get_server_time()
        print(f"Server time: {server_time}")
        client_account=client.futures_account()
        print("Account connected succesfully!")
        print(f"Total Wallet balance: {client_account.get('totalWalletBalance','N/A')} USDT")
        return True
    except BinanceAPIException as e:
        print(f"Binance API Error: {e}")
        return False
    except Exception as e:
        print(f"Connection Error: {e}")
        return False
if __name__=='__main__':
    success=test_connection()
    if(success):
        print("Connection test passed! move onto building the trading bot.")
    else:
        print("Connection test failed, Please check the api_keys.")