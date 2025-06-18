# youtube_search_backend.py
import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS # Required for CORS if your frontend is on a different domain

app = Flask(__name__)
CORS(app) # Enable CORS for requests from your AirDownloader frontend

# Configure yt-dlp for search only (no download)
# 'extract_flat': True - avoids deeper processing, just gets metadata quickly
# 'skip_download': True - ensures no actual download happens here
# 'quiet': True - suppresses console output from yt-dlp
# 'default_search': 'ytsearch' - default to YouTube search if no specific prefix
ydl_opts_search = {
    'quiet': True,
    'extract_flat': True, # Get basic info without diving deep
    'force_generic_extractor': False, # Allow specific extractors
    'skip_download': True,
    'format': 'best', # Just to get info, not relevant for flat extract
    'noplaylist': True,
}

@app.route("/")
def health_check():
    return "YouTube Search Backend is running!"

@app.route("/search", methods=["GET"])
def search_youtube():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Missing 'query' parameter."}), 400

    try:
        # Use ytsearch10 to get top 10 results
        # You can adjust the number after 'ytsearch'
        with yt_dlp.YoutubeDL(ydl_opts_search) as ydl:
            # yt-dlp's 'extract_info' will automatically handle the search
            # result['entries'] will contain a list of video metadata
            result = ydl.extract_info(f"ytsearch10:{query}", download=False)
            
            if not result or 'entries' not in result:
                return jsonify({"results": []}), 200

            # Filter for relevant video details (title, thumbnail, actual video ID for URL)
            search_results = []
            for entry in result['entries']:
                if entry.get('extractor_key') == 'Youtube' and entry.get('id'): # Ensure it's a YouTube video
                    search_results.append({
                        "title": entry.get('title', 'Unknown Title'),
                        "thumbnail": entry.          get('thumbnail') or f"https://i.ytimg.com/vi/{entry['id']}/mqdefault.jpg", # Fallback thumbnail
                        "url": f"https://www.youtube.com/watch?v={entry['id']}" # Full YouTube URL
                    })
            
            return jsonify({"results": search_results}), 200

    except Exception as e:
        print(f"Error during YouTube search: {e}")
        return jsonify({"error": "Failed to perform search. Make sure FFmpeg is installed and yt-dlp is up-to-date."}), 500

if __name__ == "__main__":
    # For local development:
    # app.run(debug=True, host="0.0.0.0", port=5000)
    # For production deployment on Koyeb, use their specified port (e.g., PORT env var)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
