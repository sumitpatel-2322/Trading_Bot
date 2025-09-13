# Binance Futures Trading Bot

**A Python trading bot I built during my learning journey! 🚀**

This is my latest project - a trading bot that connects to Binance Futures Testnet. It was super exciting to work with APIs and create both a command-line tool and a web interface!

***

## 🎯 What I Built

This bot can place buy/sell orders, check balances, and manage trades on Binance's practice environment (no real money involved, thankfully! 😅). I wanted to learn API integration and create something that looks professional.

**Features I implemented:**

- ✅ Market \& Limit order placement
- ✅ Real-time balance checking
- ✅ Order management (view and cancel)
- ✅ Price checker for crypto symbols
- ✅ Command-line interface (CLI)
- ✅ Web dashboard using Streamlit
- ✅ Proper logging and error handling

***

## 🛠️ Technologies I Used

- **Python** - Main programming language
- **python-binance** - For Binance API integration
- **Streamlit** - Web dashboard (learned this just for this project!)
- **Pandas** - Data handling and tables
- **HTML/CSS** - Custom styling for the web interface

***

## 📋 How to Run This Project

### 1. Setup (First Time)

```bash
# Clone my project
git clone <https://github.com/sumitpatel-2322/Trading_Bot>
cd binance-trading-bot

# Create virtual environment (This is important!)
python -m venv venv #using python
venv\Scripts\activate  

conda create --prefix ./venv python==3.11.11 -y #Using conda environment

# Install all the packages I used
pip install -r requirements.txt
```

### 2. Get Binance Testnet Account

1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Sign up for free (no real money needed!)
3. Create API Key \& Secret from your account
4. Create `.env` file in project folder:
```env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_secret
```


### 3. Run the Bot!

**Web Interface (my favorite!):**

```bash
python main.py --ui
```

Then open http://localhost:8501 in your browser!

**Command Line:**

```bash
# Check balance
python main.py --cli --balance

# Place a small test order
python main.py --cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```


***

## 🎮 How to Use It

### Web Dashboard

The Streamlit interface I built has tabs for:

- **Dashboard** - See your balance and stats
- **Trade** - Place buy/sell orders with a form
- **Orders** - View and cancel open orders
- **Prices** - Check current crypto prices


### Command Line

I made it simple to use from terminal:

```bash
# Basic commands I implemented
python main.py --cli --balance              # Show balance
python main.py --cli --orders               # Show open orders  
python main.py --cli --price-check --symbol BTCUSDT  # Get BTC price

# Place orders (careful, even on testnet!)
python main.py --cli --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
python main.py --cli --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3000
```


***

## 🧠 What I Learned

This project taught me so much:

- **API Integration** - First time working with financial APIs
- **Error Handling** - Learned to handle API errors properly
- **Logging** - Important for debugging trading bots
- **Code Organization** - Structured project with separate modules
- **Testing** - Wrote tests to make sure everything works

The biggest challenge was handling different error cases from Binance API.

***

## 📁 Project Structure

I organized the code like this:

```
src/
├── bot/           # Main trading logic
├── ui/            # Streamlit app and CLI 
└── utils/         # Logging and error handling

logs/              # All API calls get logged here
tests/             # My test cases
main.py           # Entry point
```


***

## ⚠️ Important Notes

- This uses **Binance TESTNET only** - no real money!
- I'm still learning, so there might be bugs 🐛
- All trades are logged in the `logs/` folder
- Built for learning purposes and portfolio

***

## 🚀 Future Improvements

Things I want to add next:

- [ ] More order types (Stop-Loss, Take-Profit)
- [ ] Price alerts and notifications
- [ ] Trading strategy automation
- [ ] Better mobile-responsive design
- [ ] Deploy to cloud (Heroku or Streamlit Cloud)

***

## 📚 Resources That Helped Me

- [Python-Binance Documentation](https://github.com/sammchardy/python-binance)
- YouTube tutorials for API integration
- Stack Overflow (saved me many times! 😊)

***

## 🤝 Feedback Welcome!

I'm still learning and would love feedback on:

- Code structure and best practices
- UI/UX improvements
- Additional features to implement
- Any bugs you find

Feel free to open issues or reach out if you want to collaborate!

***

**Thanks for checking out my project! Building this taught me so much about APIs, web development, and financial technology. Can't wait to build more cool stuff! 💻✨**

***