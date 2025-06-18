from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/search')
def search_youtube():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "No search query provided"}), 400

    try:
        # Prepare the search URL
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # Make request to YouTube with a realistic user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all script tags containing video data
        scripts = soup.find_all('script')
        video_data = []
        
        # Regular expression to find video information
        pattern = re.compile(r'{"videoRenderer":.*?"videoId":"(.*?)".*?"title":{"runs":\[{"text":"(.*?)"}].*?"thumbnail":{"thumbnails":\[.*?{"url":"(.*?)"')
        
        for script in scripts:
            if 'var ytInitialData =' in script.text:
                # Extract the JSON-like data from the script
                json_str = script.text.split('var ytInitialData =')[1].split(';')[0]
                # Find all video matches in the JSON string
                matches = pattern.finditer(json_str)
                for match in matches:
                    video_id = match.group(1)
                    title = match.group(2).replace('\\u0026', '&')
                    thumbnail = match.group(3).replace('\\u0026', '&')
                    
                    # Skip shorts and live streams
                    if 'shorts' in thumbnail.lower() or 'live' in title.lower():
                        continue
                        
                    video_data.append({
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "thumbnail": thumbnail
                    })
                
                # Limit to 15 results
                video_data = video_data[:15]
                break
        
        return jsonify({
            "success": True,
            "results": video_data
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to fetch YouTube search results"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
