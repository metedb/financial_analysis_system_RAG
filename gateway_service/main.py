from fastapi import FastAPI, HTTPException
import httpx
from config.settings import settings
from models import StockRequest, NewsRequest, FinancialsRequest, AnalysisRequest
import logging
import json
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="API Gateway",
    description="Gateway for controlling data ingestion and storage services",
    version="1.0.0"
)

# the base URLs of the services
INGESTION_SERVICE_URL = settings.INGESTION_SERVICE_URL
STORAGE_SERVICE_URL = settings.STORAGE_SERVICE_URL
ANALYSIS_SERVICE_URL = settings.ANALYSIS_SERVICE_URL

@app.get("/")
async def root():
    return {"service": "api_gateway_service", "status": "running"}



#### SAVE STOCK DATA
@app.post("/stocks")
async def fetch_and_store_stocks(request: StockRequest):
    async with httpx.AsyncClient() as client:
        # Step 1: Fetch from ingestion service
        try:
            logger.info(f"Sending request to ingestion service: {INGESTION_SERVICE_URL}/api/v1/stocks")
            logger.info(f"Request payload: {request.model_dump()}")
            
            ingestion_response = await client.post(
                f"{INGESTION_SERVICE_URL}/api/v1/stocks",
                json=request.model_dump(),
                timeout=30.0
            )
            ingestion_response.raise_for_status()
            stock_data = ingestion_response.json()
            logger.info(f"Ingestion service response: {stock_data}")
            
            # Print the structure of the data
            logger.info(f"Stock data type: {type(stock_data)}")
            if isinstance(stock_data, dict):
                logger.info(f"Stock data keys: {stock_data.keys()}")
            
            # Step 2: Store data
            logger.info(f"Sending data to storage service: {STORAGE_SERVICE_URL}/api/v1/store/stocks")
            storage_response = await client.post(
                f"{STORAGE_SERVICE_URL}/api/v1/store/stocks",
                json={"data": stock_data.get("data", []), "metadata": stock_data.get("metadata", {})},
                timeout=30.0
            )
            storage_response.raise_for_status()
            return storage_response.json()
            
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))




#### SAVE NEWS DATA
@app.post("/news")
async def fetch_and_store_news(request: NewsRequest):
    """
    Fetch news data via ingestion service and store it via storage service.
    """
    async with httpx.AsyncClient() as client:
        # Step 1: Forward request to ingestion service
        try:
            logger.info(f"Sending request to ingestion service: {INGESTION_SERVICE_URL}/api/v1/news")
            ingestion_response = await client.post(
                f"{INGESTION_SERVICE_URL}/api/v1/news",
                json=request.model_dump()
            )
            ingestion_response.raise_for_status()
            news_data = ingestion_response.json()
            logger.info("Successfully fetched news data from ingestion service")
        except httpx.RequestError as e:
            logger.error(f"Ingestion service request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ingestion service request error: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"Ingestion service HTTP error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ingestion service error: {str(e)}")

        # Step 2: Forward the fetched data to storage service
        try:
            logger.info(f"Sending data to storage service: {STORAGE_SERVICE_URL}/api/v1/store/news")
            logger.info(f"News data being sent to storage service: {news_data}")
            storage_response = await client.post(
                f"{STORAGE_SERVICE_URL}/api/v1/store/news",
                json=news_data
            )
            storage_response.raise_for_status()
            
            # Try to get JSON response, with fallback
            try:
                return storage_response.json()
            except json.JSONDecodeError:
                logger.info("Storage service returned non-JSON response")
                return {"status": "success", "message": "Data stored successfully"}
                
        except httpx.RequestError as e:
            logger.error(f"Storage service request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Storage service request error: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"Storage service HTTP error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Storage service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error with storage service: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Storage service error: {str(e)}")





#### SEARCH NEWS DATA
@app.get("/news/search")
async def search_news(query: str):
    """
    Search news data using vector similarity search
    """
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Sending search request to storage service: {STORAGE_SERVICE_URL}/api/v1/search/news")
            search_response = await client.get(
                f"{STORAGE_SERVICE_URL}/api/v1/search/news",
                params={"query": query}
            )
            search_response.raise_for_status()
            return search_response.json()

        except httpx.RequestError as e:
            logger.error(f"Search error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Search service error: {str(e)}")







### SAVE FINANCIAL STATEMENT DATA
@app.post("/financials")
async def fetch_and_store_financials(request: FinancialsRequest):
    """
    Fetch financials data via ingestion service and store it via storage service.
    """
    async with httpx.AsyncClient() as client:
        # Step 1: Forward request to ingestion service
        try:
            logger.info(f"Sending request to ingestion service for tickers: {request.tickers}")
            ingestion_response = await client.post(
                f"{INGESTION_SERVICE_URL}/api/v1/financials",
                json=request.model_dump(),
                timeout=300.0  # Increase timeout for multiple tickers
            )
            
            # Log the response status and content for debugging
            logger.info(f"Ingestion service response status: {ingestion_response.status_code}")
            logger.debug(f"Ingestion service response content: {ingestion_response.text[:1000]}")  # Log first 1000 chars
            
            ingestion_response.raise_for_status()
            financial_data = ingestion_response.json()
            
        except httpx.TimeoutException as e:
            logger.error(f"Ingestion service timeout: {str(e)}")
            raise HTTPException(
                status_code=504,
                detail=f"Ingestion service timeout after {e.timeout} seconds"
            )
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Ingestion service HTTP error: {error_detail}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ingestion service error: {error_detail}"
            )
        except httpx.RequestError as e:
            logger.error(f"Ingestion service request error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Ingestion service connection error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during ingestion: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected ingestion error: {str(e)}"
            )

        # Step 2: Forward the fetched data to storage service
        try:
            storage_response = await client.post(
                f"{STORAGE_SERVICE_URL}/api/v1/store/financials",
                json=financial_data,
                timeout=60.0
            )
            storage_response.raise_for_status()
            
            return {
                "message": "Financial data processed successfully",
                "data": storage_response.json(),
                "metadata": {
                    "tickers_processed": request.tickers,
                    "years_processed": request.years_back,
                }
            }
        except Exception as e:
            logger.error(f"Storage service error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Storage service error: {str(e)}"
            )
        




### SEARCH SQL DATA
@app.get("/sql/search")
async def search_sql(query: str):
    """
    Handle SQL query requests, forward them to the storage service.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Send SQL query request to the storage service's /search/SQL endpoint
            logger.info(f"Sending SQL search request to storage service: {STORAGE_SERVICE_URL}/api/v1/search/sql")
            sql_response = await client.get(
                f"{STORAGE_SERVICE_URL}/api/v1/search/sql", params={"query": query}
            )
            sql_response.raise_for_status()  # Raise an error for bad responses
            return sql_response.json()  # Return the SQL query results as a JSON response

        except httpx.RequestError as e:
            logger.error(f"Search error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Search service error: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error during SQL search: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
        



@app.post("/analysis")
async def get_financial_analysis(request: AnalysisRequest):
    """
    Forward financial analysis requests to the analysis service
    """
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Sending request to analysis service: {ANALYSIS_SERVICE_URL}/api/v1/analysis")
            logger.info(f"Analysis request payload: {request.model_dump()}")
            
            analysis_response = await client.post(
                f"{ANALYSIS_SERVICE_URL}/api/v1/analysis",
                json=request.model_dump(),
                timeout=300.0  # Longer timeout as LLM processing might take time
            )
            analysis_response.raise_for_status()
            return analysis_response.json()
            
        except httpx.RequestError as e:
            logger.error(f"Analysis service request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis service request error: {str(e)}")
        except httpx.HTTPError as e:
            logger.error(f"Analysis service HTTP error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error with analysis service: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis service error: {str(e)}")

        


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


