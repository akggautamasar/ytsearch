import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time
import redis
import json
from concurrent.futures import ThreadPoolExecutor
import threading

# Set up logging to stdout for Koyeb
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize Redis (replace with your Redis credentials)
redis_client = redis.Redis(
    host='your-redis-host',  # e.g., 'redis-12345.upstash.io'
    port=6379,
    password='your-redis-password',
    decode_responses=True,
    ssl=True  # Use SSL for cloud Redis providers
)

# Thread pool for async yt-dlp calls
executor = ThreadPoolExecutor(max_workers=2)

# yt-dlp configuration
ydl_opts_search = {
    'quiet': False,
    'extract_flat': True,
    'skip_download': True,
    'format': 'best',
    'noplaylist': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    },
    'no_color': True,
    'logger': logger,
    'default_search': 'ytsearch3',  # Limit to 3 results for speed
    'retries': 3,
    'socket_timeout': 10,
}

def run_ydl(query):
    """Run yt-dlp in a separate thread"""
    with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
        return ydl.extract_info(f"ytsearch:{query}", download=False)

@app.route("/")
def health_check():
    logger.debug("Health check requested")
    return "YouTube Search Backend is running!", 200

@app.route("/search", methods=["GET"])
def search_youtube():
    query = request.args.get("query")
    logger.debug(f"Incoming search request for query: '{query}'")
    print(f"--- DEBUG: Incoming search request for query: '{query}' [Thread: {threading.current_thread().name}] ---")

    if not query:
        logger.warning("Missing query parameter")
        print("--- DEBUG: Missing query parameter ---")
        return jsonify({"error": "Missing 'query' parameter."}), 400

    # Check cache
    try:
        cached = redis_client.get(f"search:{query}")
        if cached:
            logger.info(f"Cache hit for query: {query}")
            print(f"--- DEBUG: Cache hit for query: {query} ---")
            return jsonify(json.loads(cached)), 200
    except redis.RedisError as e:
        logger.error(f"Redis error: {str(e)}")
        print(f"--- DEBUG: Redis error: {str(e)} ---")

    start_time = time.time()
    try:
        # Run yt-dlp in thread pool
        result = executor.submit(run_ydl, query).result(timeout=10)
        
        if not result or 'entries' not in result:
            logger.info(f"No entries found for query: {query}")
            print(f"--- DEBUG: No entries for query: {query} ---")
            response = {"results": []}
            # Cache empty results for 10 minutes
            redis_client.setex(f"search:{query}", 600, json.dumps(response))
            return jsonify(response), 200

        search_results = [
            {
                "title": entry.get('title', 'Unknown Title'),
                "thumbnail": entry.get('thumbnail') or f"https://i.ytimg.com/vi/{entry['id']}/mqdefault.jpg",
                "url": f"https://www.youtube.com/watch?v={entry['id']}"
            }
            for entry in result['entries']
            if entry.get('extractor_key') == 'Youtube' and entry.get('id')
        ]
        
        response = {"results": search_results}
        # Cache results for 1 hour
        redis_client.setex(f"search:{query}", 3600, json.dumps(response))
        
        duration = time.time() - start_time
        logger.info(f"Search for '{query}' took {duration:.2f} seconds. Found {len(search_results)} results.")
        print(f"--- DEBUG: Search for '{query}' took {duration:.2f} seconds. Found {len(search_results)} results. ---")
        return jsonify(response), 200

    except TimeoutError:
        logger.error(f"Search for '{query}' timed out")
        print(f"--- DEBUG: Search timed out for query: {query} ---")
        return jsonify({"error": "Search took too long."}), 500
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"DownloadError for query '{query}': {str(e)}", exc_info=True)
        print(f"--- DEBUG: DownloadError: {str(e)} ---")
        return jsonify({"error": "YouTube search failed, possibly due to rate-limiting or network issues."}), 500
    except Exception as e:
        logger.error(f"Unexpected error for query '{query}': {str(e)}", exc_info=True)
        print(f"--- DEBUG: Unexpected EXCEPTION: {str(e)} ---")
        return jsonify({"error": "Failed to perform search."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting YouTube Search Backend on port {port}")
    print(f"--- DEBUG: App is starting on port {port} [Thread: {threading.current_thread().name}] ---")
    app.run(host="0.0.0.0", port=port, debug=False)
