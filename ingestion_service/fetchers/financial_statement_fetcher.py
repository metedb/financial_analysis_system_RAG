# fetchers/financial_statement_fetcher.py
import yfinance as yf
import pandas as pd
import logging
from typing import Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_company_data(ticker: str) -> pd.DataFrame:
    """
    fetch and process financial data for a single company with retry logic
    returns a single DataFrame containing both quarterly and annual data
    """
    try:
        company = yf.Ticker(ticker)
        company_name = company.info.get('longName', ticker)
        logger.info(f"Processing {company_name} ({ticker})")
        
        # first process quarterly data
        quarterly = company.quarterly_financials
        annual = company.financials
        
        if quarterly.empty and annual.empty:
            logger.warning(f"No financial data available for {ticker}")
            return pd.DataFrame()
        
        dfs = []
        
        if not quarterly.empty:
            quarterly_df = quarterly.T
            quarterly_df['Report_Type'] = 'Quarterly'
            quarterly_df['Fiscal_Quarter'] = quarterly_df.index.quarter
            quarterly_df['Fiscal_Year'] = quarterly_df.index.year
            dfs.append(quarterly_df)
        


        # then process annual data
        if not annual.empty:
            annual_df = annual.T
            annual_df['Report_Type'] = 'Annual'
            annual_df['Period'] = annual_df.index.strftime('FY %Y')
            annual_df['Fiscal_Quarter'] = 0  # 0 indicates annual
            annual_df['Fiscal_Year'] = annual_df.index.year
            dfs.append(annual_df)
        
        # combine both
        if dfs:
            combined_df = pd.concat(dfs, axis=0)
            
            # add company info
            combined_df['Ticker'] = ticker
            combined_df['Company_Name'] = company_name
            
            # calculate additional financial metrics using available data
            if 'Total Revenue' in combined_df.columns:
                if 'Net Income' in combined_df.columns:
                    combined_df['Net_Margin'] = (combined_df['Net Income'] / combined_df['Total Revenue'])
                if 'Operating Income' in combined_df.columns:
                    combined_df['Operating_Margin'] = (combined_df['Operating Income'] / combined_df['Total Revenue'])
            
            # calculate growth metrics
            for report_type in ['Quarterly', 'Annual']:
                mask = combined_df['Report_Type'] == report_type
                if report_type == 'Quarterly':
                    combined_df.loc[mask, 'Revenue_QoQ'] = combined_df.loc[mask, 'Total Revenue'].pct_change()
                else:
                    combined_df.loc[mask, 'Revenue_YoY'] = combined_df.loc[mask, 'Total Revenue'].pct_change()
            
            # clean up and format
            combined_df = combined_df.round(2)
            combined_df = combined_df.replace([float('inf'), float('-inf'), float('nan')], 0)

            logger.info(f"Successfully processed {company_name}")
            return combined_df
        
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Error processing {ticker}: {str(e)}")
        raise



async def get_company_financials(tickers: List[str]) -> dict:
    try:
        all_data = []
        failed_tickers = []
        successful_tickers = []
        
        # process each ticker
        for ticker in tickers:
            try:
                company_df = await fetch_company_data(ticker)
                if not company_df.empty:
                    all_data.append(company_df)
                    successful_tickers.append(ticker)
                else:
                    failed_tickers.append(ticker)
            except Exception as e:
                logger.error(f"Failed to process {ticker}: {str(e)}")
                failed_tickers.append(ticker)
                continue
        
        # combine all results
        if all_data:
            final_df = pd.concat(all_data, axis=0).reset_index()
            final_df = final_df.rename(columns={'index': 'Date'})
            final_df['Date'] = pd.to_datetime(final_df['Date']).dt.strftime('%Y-%m-%d')
            final_df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)

            
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
        else:
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