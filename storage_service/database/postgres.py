from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Float, Date, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from config.settings import settings
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import enum
from api.models import FinancialData


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_async_engine(settings.POSTGRES_URI)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


### stock prices table format to store in postgresql
class StockPrice(Base):
    __tablename__ = "stock_prices"
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uix_ticker_date"),
        {"schema": "public"},
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    daily_return = Column(Float)






class ReportType(enum.Enum):
    QUARTERLY = "Quarterly"
    ANNUAL = "Annual"


class BaseFinancialStatement(Base):
    """Abstract base class for financial statements"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    report_date = Column(Date, nullable=False)
    data = Column(JSON)


class QuarterlyStatement(BaseFinancialStatement):
    __tablename__ = "quarterly_statements"
    __table_args__ = (
        UniqueConstraint("ticker", "fiscal_year", "fiscal_quarter", 
                        name="uix_quarterly_ticker_year_quarter"),
        {"schema": "public"},
    )
    
    fiscal_quarter = Column(Integer, nullable=False)

class AnnualStatement(BaseFinancialStatement):
    __tablename__ = "annual_statements"
    __table_args__ = (
        UniqueConstraint("ticker", "fiscal_year", 
                        name="uix_annual_ticker_year"),
        {"schema": "public"},
    )




async def save_stocks(stock_data):
   """Save stock data to PostgreSQL"""
   async with AsyncSessionLocal() as session:
       for record in stock_data.data:
           try:
               logger.info(f"Processing {len(stock_data.data)} stock records")
               datetime_obj = datetime.fromisoformat(record["Date"])
               stock_price = StockPrice(
                   ticker=record["Ticker"],
                   date=datetime_obj.date(),
                   open=record.get("Open", 0.0),
                   high=record.get("High", 0.0),
                   low=record.get("Low", 0.0),
                   close=record.get("Close", 0.0),
                   volume=record.get("Volume", 0),
                   daily_return=record.get("Daily_Return", 0.0),
               )
               session.add(stock_price)
               await session.commit()
               logger.info("Stock data saved successfully")
           except IntegrityError:
               await session.rollback()
               logger.warning("Duplicate record detected, skipping.")
               continue
           except Exception as e:
               await session.rollback()
               logger.error(f"Error saving stock data: {str(e)}")


 
async def save_financials(financial_data: FinancialData):
    """Save financial statements to appropriate tables"""
    async with AsyncSessionLocal() as session:
        try:
            for record in financial_data.data:  
                if record["Report_Type"] == "Quarterly":
                    statement = QuarterlyStatement(
                        ticker=record["Ticker"],
                        fiscal_year=record["Fiscal_Year"],
                        fiscal_quarter=record["Fiscal_Quarter"],
                        report_date=datetime.strptime(record["Date"], "%Y-%m-%d").date(),
                        data=record
                    )
                else:  
                    statement = AnnualStatement(
                        ticker=record["Ticker"],
                        fiscal_year=record["Fiscal_Year"],
                        report_date=datetime.strptime(record["Date"], "%Y-%m-%d").date(),
                        data=record
                    )
                session.add(statement)
            await session.commit()
            logger.info("Financial data saved successfully")
            return {"message": "Data saved successfully"}
        except IntegrityError as e:
            await session.rollback()
            logger.warning(f"Duplicate financial statement detected: {str(e)}")
            return {"message": "Duplicate records detected"}
        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving financial data: {str(e)}")
            raise





        
