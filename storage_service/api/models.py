from pydantic import BaseModel
from typing import List, Dict, Any

class StockData(BaseModel):
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class NewsData(BaseModel):
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class FinancialData(BaseModel):
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]