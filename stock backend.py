tickers = ["GOOGL", "XOM", "TSLA", "T","KO","TWTR", "PYPL", "INTC"]
import yfinance as yf

def render_data(ticker, resolution = ["1d", "2010-1-1", "2022-2-1"]):
	try:
		tick = yf.Ticker(ticker)
		return tick.history(period = resolution[0], start = resolution[1], end = resolution[2])
	except:
		print("Invalid ticker.")
		return

def guess_price(ticker, price):
	print(render_data(ticker))
	