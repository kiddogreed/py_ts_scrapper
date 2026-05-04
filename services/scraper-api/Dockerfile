# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install system deps for lxml + Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
# WHY only chromium? Firefox/WebKit add ~1 GB. Chromium covers 99% of use cases.
# Add --with-deps to install OS-level browser dependencies.
RUN playwright install chromium --with-deps

# Copy source
COPY . .

# Mount point for shared config (proxies, fingerprints)
VOLUME ["/app/shared"]

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
