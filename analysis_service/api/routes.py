# api/routes.py
from fastapi import APIRouter, HTTPException
import httpx
from .model.financial_analysis import get_financial_analysis
from pydantic import BaseModel
from typing import List, Optional
from .model.graph.tools.sql_tool import create_enhanced_sql_toolkit
from config.settings import settings
from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinanceQuery(BaseModel):
    query: str 

router = APIRouter(prefix="/api/v1")  


@router.post("/analysis")
async def financial_analysis(request: FinanceQuery):
    """
    Financial analysis service
    """
    try:
        result = await get_financial_analysis(
            query=request.query,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


##quick health check
@router.get("/test/sql")
async def test_sql_connection():
    print("Starting test_sql_connection")  
    try:
        print("Creating toolkit") 
        sql_tools = create_enhanced_sql_toolkit(
            endpoint_url=f"{settings.GATEWAY_URI}/sql/search",
            llm=None
        )
        print(f"Tools created: {sql_tools}")  
        
        query_tool = sql_tools[0]
        print(f"Using query tool: {query_tool}") 
        
        test_query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        print(f"Running query: {test_query}")  
        result = await query_tool._arun(test_query)
        
        return {
            "status": "success",
            "message": "SQL connection working",
            "test_result": result
        }
        
    except Exception as e:
        logger.error(f"SQL test failed: {str(e)}")
        return {
            "status": "error",
            "message": f"SQL test failed: {str(e)}"
        }



@router.get("/health")
async def health_check():
    """
    Check if the service is healthy
    """
    return {
        "status": "healthy",
        "service": "analysis_service"
    }