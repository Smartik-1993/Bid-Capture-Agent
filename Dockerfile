FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure data directory exists for SQLite
RUN mkdir -p data

EXPOSE 8000

# Run uvicorn using the PORT environment variable provided by hosting platforms (Render, Railway, Cloud Run, etc.)
CMD ["sh", "-c", "uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
