FROM python:3.12-slim

# Install system dependencies required by Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 \
    libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 \
    libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libxss1 libxtst6 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN python -m playwright install --with-deps chromium

# Copy project source
COPY . /app/

# Install the project itself in editable mode
RUN pip install --no-cache-dir -e .

# Default command: run the FastAPI audit API
CMD ["uvicorn", "agentic-ui-auditor.api:app", "--host", "0.0.0.0", "--port", "80"]
