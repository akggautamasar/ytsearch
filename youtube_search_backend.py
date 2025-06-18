# youtube_search_backend.py
import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time # <--- ADDED THIS LINE: Import the time module

# Set up logging for debugging and performance monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app) # Enable CORS for frontend requests

# Configure yt-dlp for search
ydl_opts_search = {
    'quiet': True,
    'extract_flat': True, # Get metadata only
    'skip_download': True, # No downloading
    'format': 'best',
    'noplaylist': True,
    # 'default_search': 'ytsearch10', # Removed or commented out, as 'ytsearch:' prefix is used explicitly below
    'http_headers': { # Mimic browser to reduce rate-limiting / blocking
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
}

@app.route("/")
def health_check():
    return "YouTube Search Backend is running!", 200

@app.route("/search", methods=["GET"])
def search_youtube():
    query = request.args.get("query")
    if not query:
        logger.warning("Search request received with missing 'query' parameter.")
        return jsonify({"error": "Missing 'query' parameter."}), 400

    start_time = time.time() # Measure performance
    logger.info(f"Received search request for query: '{query}'") # Log incoming request

    try:
        with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
            # Use 'ytsearch:' prefix directly to ensure search functionality
            result = ydl.extract_info(f"ytsearch:{query}", download=False)
            
            if not result or 'entries' not in result:
                logger.info(f"yt-dlp returned no entries for query: '{query}'")
                return jsonify({"results": []}), 200

            search_results = [
                {
                    "title": entry.get('title', 'Unknown Title'),
                    "thumbnail": entry.get('thumbnail') or f"https://i.ytimg.com/vi/{entry['id']}/mqdefault.jpg", # Fallback thumbnail
                    "url": f"https://www.youtube.com/watch?v={entry['id']}" # Full YouTube URL
                }
                for entry in result['entries']
                if entry.get('extractor_key') == 'Youtube' and entry.get('id') # Ensure it's a YouTube video with an ID
            ]
            
            logger.info(f"Search for '{query}' took {time.time() - start_time:.2f} seconds. Found {len(search_results)} results.")
            return jsonify({"results": search_results}), 200

    except Exception as e:
        logger.error(f"Error during YouTube search for query '{query}': {str(e)}", exc_info=True) # exc_info to log full traceback
        return jsonify({"error": "Failed to perform search. Please try again later. If the issue persists, the service might be temporarily blocked or facing a network issue."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000)) # Default to 8000 for Koyeb
    logger.info(f"Starting YouTube Search Backend on port {port}")
    app.run(host="0.0.0.0", port=port)
