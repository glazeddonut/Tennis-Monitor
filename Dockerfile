FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies required by Playwright / headless browsers
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        libnss3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libx11-6 \
        libxss1 \
        libxcomposite1 \
        libxrandr2 \
        libasound2 \
        libpangocairo-1.0-0 \
        libgtk-3-0 \
        libgbm1 \
        libxshmfence1 \
        fonts-liberation \
        libwoff1 \
        libopus0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium). Use python -m playwright to ensure the package CLI is available.
RUN python -m playwright install chromium

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh || true

# Create logs directory so it can be mounted as a volume
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Ensure Python can import from src/
ENV PYTHONPATH=/app/src

ENTRYPOINT ["/app/entrypoint.sh"]
