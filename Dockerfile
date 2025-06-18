# Use Python 3.10 to match your previous environment
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install FFmpeg and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8000 (Koyeb’s default)
EXPOSE 8000

# Run Gunicorn with 4 workers, binding to the PORT environment variable
# Fallback to 8000 if PORT is not set
CMD ["sh", "-c", "gunicorn -w 4 --bind 0.0.0.0:${PORT:-8000} youtube_search_backend:app"]
