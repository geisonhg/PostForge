# PostForge — Dockerfile
# Multi-stage build for lean production image

FROM python:3.11-slim AS base

# System dependencies for Pillow and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    libffi-dev \
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create required directories
RUN mkdir -p \
    input/inbox \
    input/processed \
    output/final_posts \
    output/captions \
    output/metadata \
    output/logs \
    config/brands \
    assets/confluex \
    fonts

# Non-root user for security
RUN useradd -m -u 1000 postforge && chown -R postforge:postforge /app
USER postforge

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
