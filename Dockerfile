# Use a slim Python base image for smaller size, based on Debian Buster
FROM python:3.9-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Install FFmpeg and other necessary system dependencies
# FFmpeg is crucial for yt-dlp's audio/video processing capabilities.
# --no-install-recommends helps keep the image size down.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file first to leverage Docker's build cache
# If requirements.txt doesn't change, this step won't re-run on subsequent builds
COPY requirements.txt .

# Install Python dependencies from requirements.txt
# --no-cache-dir ensures pip doesn't store build artifacts, further reducing image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port that Gunicorn will listen on
# Koyeb typically exposes port 8000. Your Python script's default is 5000.
# The CMD will use the PORT environment variable provided by Koyeb.
EXPOSE 5000 # Keep 5000 here as your Python app runs on this by default.

# Command to run the Flask application using Gunicorn via the Python module system.
# This is more robust than directly calling 'gunicorn'.
# It binds to 0.0.0.0:$(PORT) which will be set by Koyeb (usually 8000).
# 'youtube_search_backend:app' refers to the 'app' Flask instance within 'youtube_search_backend.py'.
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:${PORT}", "youtube_search_backend:app"]
