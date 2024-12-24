from .index_manager import IndexManager
from llama_index.core import Document
from typing import List
import pymongo
from config.settings import settings
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
import logging

logger = logging.getLogger("uvicorn")
index_manager = IndexManager()

atlas_client = AsyncIOMotorClient(settings.MONGODB_URI)
news_collection = atlas_client[settings.MONGODB_DB]["news"]


###create document objects from raw data
async def create_news_documents(news_data) -> List[Document]:
    print(f"News data received for document creation: {news_data}")
    documents = []
    try:
        for article in news_data.data:
            feed = article.get("feed", [])
            for feed_item in feed:
                doc = Document(
                    text=feed_item.get("summary", "No summary available"),
                    metadata={
                        "source": feed_item.get("source", "Unknown source"),
                        "date": feed_item.get("time_published", "Unknown date"),
                        "title": feed_item.get("title", "No title provided"),
                        "url": feed_item.get("url", "No URL provided"),
                        "overall_sentiment_label": feed_item.get("overall_sentiment_label", "Unknown sentiment"),
                        "overall_sentiment_score": feed_item.get("overall_sentiment_score", 0),
                    },
                )
                documents.append(doc)
    except Exception as e:
        raise Exception(f"Error creating documents: {str(e)}")
    return documents



async def save_news(news_data):
    """Save news data and create vector embeddings"""
    try:
        logger.info("Starting to save news data...")
        
        # 1. save raw data to MongoDB 
        logger.info(f"Inserting raw news data into MongoDB: {len(news_data.data)} items")
        result = await news_collection.insert_many(news_data.data)
        logger.info(f"Successfully inserted {len(result.inserted_ids)} items into MongoDB")

        # 2. check if there's any content in the feeds
        has_content = any(article.get("feed") for article in news_data.data)
        
        if not has_content:
            logger.info("No news content found in feeds - skipping vector indexing")
            return {
                "status": "success",
                "message": "Empty news data saved to MongoDB",
                "raw_docs_saved": len(result.inserted_ids),
                "vectors_created": 0,
                "details": "No content available for vector indexing"
            }

        # 3. if we content isn't empty, index it and store
        documents = await create_news_documents(news_data)
        if documents:
            logger.info(f"Creating and saving vector index with {len(documents)} documents")
            index = await index_manager.save_atlas_index(documents)
            logger.info("Successfully created and saved vector index")
            return {
                "status": "success",
                "message": "News data stored successfully",
                "raw_docs_saved": len(result.inserted_ids),
                "vectors_created": len(documents),
                "details": "Data saved to both MongoDB and vector index"
            }

    except Exception as e:
        logger.error(f"Failed to save news data: {str(e)}")
        if "No index in storage context" in str(e):
            # Convert to more user-friendly error message
            raise HTTPException(
                status_code=500, 
                detail="Unable to create vector index due to empty content"
            )
        raise HTTPException(status_code=500, detail=str(e))

    


### to test if atlas server works
async def test_mongodb_connection():
    """Test the connection to MongoDB"""
    try:
        server_info = atlas_client.server_info()
        databases = atlas_client.list_database_names()
        
        return {
            "message": "MongoDB connection successful",
            "server_info": server_info,
            "databases": databases
        }
    except pymongo.errors.ServerSelectionTimeoutError as e:
        raise Exception(f"MongoDB connection failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error while testing MongoDB connection: {str(e)}")

    


