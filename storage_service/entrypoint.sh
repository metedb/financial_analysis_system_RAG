#!/bin/bash
# Create directory structure
mkdir -p /app/storage/news_index
mkdir -p /app/chroma_db

chmod -R 777 /app/storage
exec "$@"