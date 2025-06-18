FROM python:3.9-slim-buster

WORKDIR /app

# Install FFmpeg (optional, for future-proofing)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run Gunicorn with verbose logging
CMD ["gunicorn", "-w", "2", "--bind", "0.0.0.0:${PORT:-8000}", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-", "--timeout", "30", "youtube_search_backend:app"]
