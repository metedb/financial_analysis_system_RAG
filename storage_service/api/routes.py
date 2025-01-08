# storage_service/api/routes.py
import logging
from fastapi import APIRouter, HTTPException
from .models import StockData, NewsData, FinancialData
from database.postgres import save_stocks, save_financials
from database.mongodb_atlas import save_news
from database.index_manager import IndexManager
index_manager = IndexManager()
from sqlalchemy import text as sql_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")



###STORE STOCKS DATA TO POSTGRESQL
@router.post("/store/stocks")
async def store_stocks(data: StockData):
    try:
        logger.info("Received request at /store/stocks")
        logger.info(f"Received data: {data}")
        logger.info(f"Received data type: {type(data)}")
        result = await save_stocks(data)
        logger.info(f"Save result: {result}")
        return {"message": "Stocks data stored successfully", "details": result}
    except Exception as e:
        logger.error(f"Error in store_stocks: {str(e)}")
        logger.exception("Full traceback:")  
        raise HTTPException(status_code=500, detail=str(e))




###STORE FINANCIAL STATEMENT DATA TO POSTGRESQL
@router.post("/store/financials")
async def store_financials(data: FinancialData):
    try:
        result = await save_financials(data)
        return {"message": "Financial data stored successfully", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


from database.postgres import AsyncSessionLocal



### SEARCH SQL DATABASE
@router.get("/search/sql")
async def search_sql(query: str):
    """
    Handle SQL query and execute it against PostgreSQL.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        async with AsyncSessionLocal() as session:
            sql_query = sql_text(query)
            
            # For SELECT queries
            if query.strip().lower().startswith("select"):
                result = await session.execute(sql_query)
                rows = result.fetchall()
                columns = result.keys()
                
                return {
                    "results": [dict(r._mapping) for r in rows],
                    "columns": list(columns),
                    "row_count": len(rows),
                    "query_type": "SELECT"
                }
            else:
                await session.execute(sql_query)
                await session.commit()
                return {
                    "message": "Statement executed successfully",
                    "query_type": "DML/DDL"
                }
                
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")



### STORE NEWS TO LOCAL DISK VIA CHROMADB VECTOR EMBEDDINGS
@router.post("/store/news")
async def store_news(data: NewsData):
    try:
        result = await save_news(data)
        return {"message": "News data stored successfully", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



### SEARCH NEWS VIA LLAMAINDEX RETRIEVERS
@router.get("/search/news")
async def search_news(query: str, top_k: int = 5):
    try:
        index = await index_manager.load_index()
        if not index:
            raise HTTPException(status_code=404, detail="News index not found")
            
        retriever = index.as_retriever(similarity_top_k = top_k)
        
        nodes = retriever.retrieve(query)
        
        return {
            "results": [
                {
                    "text": node.node.text, 
                    "metadata": node.node.metadata,  
                    "score": node.score 
                }
                for node in nodes
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))