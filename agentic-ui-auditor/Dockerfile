FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl gnupg ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 \
    libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 \
    libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libxss1 libxtst6 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ../requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY .. /app/
RUN pip install --no-cache-dir -e .

RUN python -m playwright install --with-deps chromium

WORKDIR /app/agentic-ui-auditor

EXPOSE 80

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "80"]
