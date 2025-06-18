# youtube_search_backend.py
import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time

# Set up logging for debugging and performance monitoring
# Ensure logs go to stdout for Koyeb to capture them
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app) # Enable CORS for frontend requests

# Configure yt-dlp for search
ydl_opts_search = {
    'quiet': False, # <--- TEMPORARILY SET TO FALSE FOR DEBUGGING!
    'extract_flat': True, # Get metadata only
    'skip_download': True, # No downloading
    'format': 'best',
    'noplaylist': True,
    'http_headers': { # Mimic browser to reduce rate-limiting / blocking
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
    'no_color': True, # Disable color codes in logs if they cause issues with log viewers
}

@app.route("/")
def health_check():
    return "YouTube Search Backend is running!", 200

@app.route("/search", methods=["GET"])
def search_youtube():
    query = request.args.get("query")
    # Raw print for extreme logging test
    print(f"--- DEBUG: Incoming search request for query: '{query}' ---") # <--- ADDED RAW PRINT

    if not query:
        logger.warning("Search request received with missing 'query' parameter.")
        print("--- DEBUG: Missing query parameter. ---") # <--- ADDED RAW PRINT
        return jsonify({"error": "Missing 'query' parameter."}), 400

    start_time = time.time()
    logger.info(f"Received search request for query: '{query}'")

    try:
        with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
            # yt-dlp will now print its own debug info to stdout because 'quiet' is False
            result = ydl.extract_info(f"ytsearch:{query}", download=False)
            
            if not result or 'entries' not in result:
                logger.info(f"yt-dlp returned no entries for query: '{query}'")
                print(f"--- DEBUG: yt-dlp found no entries for query: '{query}' ---") # <--- ADDED RAW PRINT
                return jsonify({"results": []}), 200

            search_results = [
                {
                    "title": entry.get('title', 'Unknown Title'),
                    "thumbnail": entry.get('thumbnail') or f"https://i.ytimg.com/vi/{entry['id']}/mqdefault.jpg",
                    "url": f"https://www.youtube.com/watch?v={entry['id']}"
                }
                for entry in result['entries']
                if entry.get('extractor_key') == 'Youtube' and entry.get('id')
            ]
            
            logger.info(f"Search for '{query}' took {time.time() - start_time:.2f} seconds. Found {len(search_results)} results.")
            print(f"--- DEBUG: Successfully processed search for '{query}'. Found {len(search_results)} results. ---") # <--- ADDED RAW PRINT
            return jsonify({"results": search_results}), 200

    except Exception as e:
        logger.error(f"Error during YouTube search for query '{query}': {str(e)}", exc_info=True)
        print(f"--- DEBUG: EXCEPTION caught during search: {str(e)} ---") # <--- ADDED RAW PRINT
        return jsonify({"error": "Failed to perform search. Please try again later. If the issue persists, the service might be temporarily blocked or facing a network issue."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting YouTube Search Backend on port {port}")
    print(f"--- DEBUG: App is starting on port {port} ---") # <--- ADDED RAW PRINT
    app.run(host="0.0.0.0", port=port)
