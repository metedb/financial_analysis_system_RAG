from llama_index.core import StorageContext, load_index_from_storage, VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb
import os
from sqlalchemy import make_url
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy.ext.asyncio import create_async_engine
from config.settings import settings
from llama_index.core import Document
import logging
from llama_index.core.graph_stores import SimpleGraphStore
import json


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_async_engine(settings.POSTGRES_URI)


###CLASS TO TURN RAW DATA TO VECTOR EMBEDDINGS AND STORE THEM
class IndexManager:
    def __init__(self):
        # paths to store 
        self.persist_dir = "/app/storage"
        self.chroma_dir = "/app/chroma_db"
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)

    async def save_atlas_index(self, documents):  
        """Create and save index to disk"""
        try:
            index_dir = os.path.join(self.persist_dir)
            os.makedirs(index_dir, exist_ok=True)
            
            docstore_path = os.path.join(index_dir, "docstore.json")
            if not os.path.exists(docstore_path) or os.path.getsize(docstore_path) == 0:
                initial_json = {
                    "docstore/docs": {},
                    "docstore/ref_doc_info": {},
                    "docstore/metadata": {}
                }
                with open(docstore_path, 'w') as f:
                    json.dump(initial_json, f)
            
            print(f"Ensured index directory exists: {index_dir}")
            
            chroma_collection = self.chroma_client.get_or_create_collection("main_collection")
            
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store,
                persist_dir=index_dir
            )
            
            index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=storage_context,
                    embed_model=OpenAIEmbedding(),
                    show_progress=True
                )
            
            print("Vector store index updated successfully.")
            
            # persist index to use later
            print(f"Persisting index to: {index_dir}")
            index.storage_context.persist()
            print("Index persisted successfully.")
            return index
            
        except Exception as e:
            print(f"Error during save_index: {str(e)}")
            raise Exception(f"Error saving index: {str(e)}")
        


    ### load index directly from persisted storage
    async def load_index(self):
        try:
            index_dir = self.persist_dir
            
            if not os.path.exists(index_dir):
                raise FileNotFoundError(f"Index directory '{index_dir}' does not exist.")
                
            chroma_collection = self.chroma_client.get_or_create_collection("main_collection")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store,
                persist_dir=index_dir,
                graph_store=SimpleGraphStore(),
            )
            
            index = load_index_from_storage(storage_context=storage_context)
            
            if index is None:
                raise ValueError("Index could not be loaded from storage context")
                
            return index
            
        except Exception as e:
            logger.error(f"Error in load_index: {str(e)}")
            raise Exception(f"Error loading index: {str(e)}")
