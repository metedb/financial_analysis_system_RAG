from pydantic import BaseModel
from typing import List, Optional

class StockRequest(BaseModel):
    tickers: List[str]
    period: str
    interval: str 

class NewsRequest(BaseModel):
    query_type: str
    values: List[str]
    api_key: Optional[str] = None

class FinancialsRequest(BaseModel):
    tickers: List[str]
    years_back: Optional[int] = 5

class AnalysisRequest(BaseModel):
    query: str