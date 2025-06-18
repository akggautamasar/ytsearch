from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import yt_dlp
import logging
import asyncio
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube Search Backend")

# Enable CORS to allow requests from the front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to specific origins
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Response model
class VideoResult(BaseModel):
    title: str
    url: str
    thumbnail: str

class SearchResponse(BaseModel):
    results: List[VideoResult]

# Cache for search results (in-memory, simple)
cache = {}

async def run_yt_dlp(query: str) -> List[dict]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,  # Don't download, just extract metadata
        "force_generic_extractor": False,
        "max_entries": 10,  # Limit to 10 results
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch10:{query}"  # Search YouTube with max 10 results
            result = ydl.extract_info(search_query, download=False)
            return result.get("entries", [])
    except Exception as e:
        logger.error(f"yt-dlp error for query '{query}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search", response_model=SearchResponse)
async def search_videos(query: str):
    if not query or query.strip() == "":
        raise HTTPException(status_code=400, detail="Query parameter is required")

    query = query.strip()
    cache_key = query.lower()

    # Check cache
    if cache_key in cache:
        logger.info(f"Returning cached results for query: {query}")
        return SearchResponse(results=cache[cache_key])

    try:
        # Run yt-dlp in a separate thread to avoid blocking
        entries = await asyncio.to_thread(run_yt_dlp, query)
        
        results = []
        for entry in entries:
            if not entry.get("url") or not entry.get("title"):
                continue
            video_id = entry.get("id", "")
            thumbnail = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else ""
            results.append(
                VideoResult(
                    title=entry["title"],
                    url=entry["url"],
                    thumbnail=thumbnail,
                )
            )
        
        # Cache results for 1 hour
        cache[cache_key] = results
        # Limit cache size to prevent memory issues
        if len(cache) > 100:
            cache.pop(next(iter(cache)))

        logger.info(f"Found {len(results)} results for query: {query}")
        return SearchResponse(results=results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error for query '{query}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
