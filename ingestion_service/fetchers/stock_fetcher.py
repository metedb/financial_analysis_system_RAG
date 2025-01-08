# fetchers/stock_fetcher.py
import yfinance as yf
import pandas as pd
import asyncio
import logging
from typing import List


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  

async def fetch_single_stock(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetch data for a single stock with retry logic"""
    stock = yf.Ticker(ticker)
    company_name = stock.info.get('longName', ticker)
    stock_data = await asyncio.to_thread(stock.history, period=period, interval=interval, timeout = 15)
    
    # basic info
    stock_data['Ticker'] = ticker
    stock_data['Company_Name'] = company_name
    
    # calculate metrics
    stock_data['Daily_Return'] = stock_data['Close'].pct_change() * 100
    stock_data['Trading_Range'] = stock_data['High'] - stock_data['Low']
    stock_data.index = pd.to_datetime(stock_data.index)  # ensure the index is in datetime format




    
    # fill NaN and round
    stock_data = stock_data.fillna(0)
    numerical_columns = ['Open', 'High', 'Low', 'Close', 'Daily_Return', 'Trading_Range']
    stock_data[numerical_columns] = stock_data[numerical_columns].round(2)
    
    return stock_data

async def get_stock_data(tickers: List[str], period: str, interval: str) -> dict:  
    """Get stock data for multiple tickers with error handling"""
    try:
        tasks = [fetch_single_stock(ticker, period, interval) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        combined_data = []
        failed_tickers = []
        
        for ticker, result in zip(tickers, results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {ticker}: {str(result)}")
                failed_tickers.append(ticker)
                continue
            combined_data.append(result)
        
        if combined_data:
            final_df = pd.concat(combined_data, axis=0)
            final_df = final_df.reset_index()
            
            return {
                "data": final_df.to_dict(orient='records'),
                "metadata": {
                    "successful_tickers": [t for t in tickers if t not in failed_tickers],
                    "failed_tickers": failed_tickers,
                    "total_records": len(final_df)
                }
            }
        else:
            return {
                "data": [],
                "metadata": {
                    "successful_tickers": [],
                    "failed_tickers": failed_tickers,
                    "total_records": 0
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to fetch stock data: {str(e)}")
        raise