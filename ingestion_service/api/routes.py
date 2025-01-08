# api/routes.py
from fastapi import APIRouter, HTTPException
import httpx
from .models import StockRequest, NewsRequest, FinancialsRequest
from fetchers.stock_fetcher import get_stock_data
from fetchers.news_fetcher import get_news_batch
from fetchers.financial_statement_fetcher import get_company_financials

router = APIRouter(prefix="/api/v1")  


@router.post("/stocks")
async def fetch_stocks(request: StockRequest):
    try:
        result = await get_stock_data(
            tickers=request.tickers,
            period=request.period,
            interval=request.interval
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/news")
async def fetch_news(request: NewsRequest):
    try:
        result = await get_news_batch(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/financials")
async def fetch_financials(request: FinancialsRequest):
    try:
        result = await get_company_financials(
            tickers=request.tickers,
            years_back=request.years_back
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



###endpoint to check if service works
@router.get("/health")
async def health_check():
    """
    Check if the service is healthy
    """
    return {
        "status": "healthy",
        "service": "ingestion_service"
    }