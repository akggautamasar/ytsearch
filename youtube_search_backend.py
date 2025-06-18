import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Set up logging for debugging and performance monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Configure yt-dlp for search
ydl_opts_search = {
    'quiet': True,
    'extract_flat': True,  # Get metadata only
    'skip_download': True,  # No downloading
    'format': 'best',
    'noplaylist': True,
    'default_search': 'ytsearch10',  # Default to top 10 results
    'http_headers': {  # Mimic browser to reduce rate-limiting
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
        return jsonify({"error": "Missing 'query' parameter."}), 400

    start_time = time.time()  # Measure performance
    try:
        with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
            result = ydl.extract_info(f"ytsearch:{query}", download=False)
            
            if not result or 'entries' not in result:
                logger.info(f"No results for query: {query}")
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
            
            logger.info(f"Search for '{query}' took {time.time() - start_time:.2f} seconds")
            return jsonify({"results": search_results}), 200

    except Exception as e:
        logger.error(f"Error during YouTube search: {str(e)}")
        return jsonify({"error": "Failed to perform search. Try again later."}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 for Koyeb
    app.run(host="0.0.0.0", port=port)
