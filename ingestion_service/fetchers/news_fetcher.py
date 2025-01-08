# fetchers/news_fetcher.py
import aiohttp
import logging
from datetime import datetime
from typing import Dict, Optional, List, Literal
from pydantic import BaseModel
import asyncio

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NewsRequest(BaseModel):
    query_type: Literal['company', 'industry']
    values: List[str]  # either tickers or topics
    api_key: str


async def fetch_news(
    session: aiohttp.ClientSession,
    api_key: str,
    query_type: str,
    value: str
) -> Optional[Dict]:
    """
    unified function to fetch news for either company or industry
    """
    param_key = "tickers" if query_type == "company" else "topics"
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&{param_key}={value}&apikey={api_key}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.debug(f"Response for {value}: {data}") 

                
                # check for API limit
                if "Note" in data:
                    logger.warning(f"API limit reached for {value}: {data['Note']}")
                    raise Exception("API limit reached")
                
                news_data = {
                    'query_type': query_type,
                    'value': value,
                    'feed': data.get('feed', []),
                    'timestamp': datetime.now().isoformat()
                }
                logger.info(f"Successfully fetched {query_type} news for {value}")
                return news_data
            else:
                logger.error(f"Failed to fetch {query_type} news for {value}: Status {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching {query_type} news for {value}: {str(e)}")
        raise




async def get_news_batch(request: NewsRequest) -> dict:
    """
    fetch news for multiple companies or industries with enhanced error handling and metadata
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for value in request.values:
            task = fetch_news(session, request.api_key, request.query_type, value)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        news_data = []
        failed_values = []
        successful_values = []
        
        for value, result in zip(request.values, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to get {request.query_type} news for {value}: {str(result)}")
                failed_values.append(value)
                continue
            if result:
                news_data.append(result)
                successful_values.append(value)

        return {
            "data": news_data,
            "metadata": {
                "query_type": request.query_type,
                "successful_values": successful_values,
                "failed_values": failed_values,
                "total_articles": sum(len(item['feed']) for item in news_data),
                "timestamp": datetime.now().isoformat()
            }
        }