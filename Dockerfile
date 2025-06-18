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
# Koyeb typically exposes port 8000, but you can configure Gunicorn to use any port,
# and Koyeb will automatically map it. We'll stick to 5000 as per your Python code's default.
EXPOSE 5000

# Command to run the Flask application using Gunicorn, a production-ready WSGI server.
# It binds to 0.0.0.0:5000 (accessible from outside the container on that port).
# 'youtube_search_backend:app' refers to the 'app' Flask instance within 'youtube_search_backend.py'.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "youtube_search_backend:app"]
