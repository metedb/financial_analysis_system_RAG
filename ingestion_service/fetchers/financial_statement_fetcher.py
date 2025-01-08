import yfinance as yf
import pandas as pd
import logging
from typing import List
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_company_data(ticker: str, years_back: int = 5) -> pd.DataFrame:
    """
    Fetch and process financial data for a single company with time period control
    
    Args:
        ticker (str): Company ticker symbol
        years_back (int): Number of years of historical data to fetch
        
    Returns:
        pd.DataFrame: Processed financial data
    """
    try:
        # calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years_back * 365)
        
        company = yf.Ticker(ticker)
        company_name = company.info.get('longName', ticker)
        logger.info(f"Processing {company_name} ({ticker}) from {start_date.year} to {end_date.year}")
        
        quarterly = company.quarterly_financials
        annual = company.financials
        
        if quarterly.empty and annual.empty:
            logger.warning(f"No financial data available for {ticker}")
            return pd.DataFrame()
        
        dfs = []
        
        if not quarterly.empty:
            quarterly_df = quarterly.T
            quarterly_df = quarterly_df[
                (quarterly_df.index >= start_date) & 
                (quarterly_df.index <= end_date)
            ]
            quarterly_df['Report_Type'] = 'Quarterly'
            quarterly_df['Fiscal_Quarter'] = quarterly_df.index.quarter
            quarterly_df['Fiscal_Year'] = quarterly_df.index.year
            dfs.append(quarterly_df)

        if not annual.empty:
            annual_df = annual.T
            annual_df = annual_df[
                (annual_df.index >= start_date) & 
                (annual_df.index <= end_date)
            ]
            annual_df['Report_Type'] = 'Annual'
            annual_df['Fiscal_Quarter'] = 0  # 0 indicates annual
            annual_df['Fiscal_Year'] = annual_df.index.year
            dfs.append(annual_df)
            
        if dfs:
            combined_df = pd.concat(dfs, axis=0)
            combined_df = combined_df.replace([float('inf'), float('-inf'), float('nan')], 0)
            
            # add company info
            combined_df['Ticker'] = ticker
            combined_df['Company_Name'] = company_name
            
            # calculate additional financial metrics using available data
            if 'Total Revenue' in combined_df.columns and combined_df['Total Revenue'].any():
                if 'Net Income' in combined_df.columns:
                    combined_df['Net_Margin'] = (combined_df['Net Income'] / combined_df['Total Revenue']).replace([float('inf'), float('-inf')], 0).fillna(0)
                if 'Operating Income' in combined_df.columns:
                    combined_df['Operating_Margin'] = (combined_df['Operating Income'] / combined_df['Total Revenue']).replace([float('inf'), float('-inf')], 0).fillna(0)
                
            # calculate growth metrics
            for report_type in ['Quarterly', 'Annual']:
                mask = combined_df['Report_Type'] == report_type
                if report_type == 'Quarterly':
                    combined_df.loc[mask, 'Revenue_QoQ'] = combined_df.loc[mask, 'Total Revenue'].pct_change().replace([float('inf'), float('-inf')], 0).fillna(0)
                else:
                    combined_df.loc[mask, 'Revenue_YoY'] = combined_df.loc[mask, 'Total Revenue'].pct_change().replace([float('inf'), float('-inf')], 0).fillna(0)
            
            combined_df = combined_df.round(2)
            combined_df = combined_df.replace([float('inf'), float('-inf'), float('nan')], 0)
            
            logger.info(f"Successfully processed {company_name}")
            return combined_df
            
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Error processing {ticker}: {str(e)}")
        raise



async def get_company_financials(tickers: List[str], years_back: int = 5) -> dict:
    """
    Fetch financial data for multiple companies with period control
    """
    try:
        all_data = []
        failed_tickers = []
        successful_tickers = []
        
        for ticker in tickers:
            try:
                company_df = await fetch_company_data(ticker, years_back)
                if not company_df.empty:
                    # clean the DataFrame before adding to list
                    company_df = company_df.replace([float('inf'), float('-inf'), float('nan')], 0)
                    all_data.append(company_df)
                    successful_tickers.append(ticker)
                else:
                    failed_tickers.append(ticker)
            except Exception as e:
                logger.error(f"Failed to process {ticker}: {str(e)}")
                failed_tickers.append(ticker)
                continue
        
        if all_data:
            # concatenate and clean again
            final_df = pd.concat(all_data, axis=0)
            final_df = final_df.replace([float('inf'), float('-inf'), float('nan')], 0)
            
            # reset index and format date
            final_df = final_df.reset_index()
            final_df = final_df.rename(columns={'index': 'Date'})
            final_df['Date'] = pd.to_datetime(final_df['Date']).dt.strftime('%Y-%m-%d')
            
            # sort data
            final_df = final_df.sort_values(
                by=['Ticker', 'Fiscal_Year', 'Fiscal_Quarter', 'Report_Type'],
                ascending=[True, False, False, True]
            )
            
            # final cleaning before conversion to dict
            final_df = final_df.replace([float('inf'), float('-inf'), float('nan')], 0)
            
            return {
                "data": final_df.to_dict(orient='records'),
                "metadata": {
                    "successful_tickers": successful_tickers,
                    "failed_tickers": failed_tickers,
                    "total_records": len(final_df),
                    "periods_covered": {
                        "earliest": final_df['Date'].min(),
                        "latest": final_df['Date'].max()
                    }
                }
            }
        
        return {
            "data": [],
            "metadata": {
                "successful_tickers": [],
                "failed_tickers": failed_tickers,
                "total_records": 0,
                "periods_covered": {
                    "earliest": None,
                    "latest": None
                }
            }
        }
            
    except Exception as e:
        logger.error(f"Failed to process financial data: {str(e)}")
        raise