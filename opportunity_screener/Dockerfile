FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY opportunity_screener/requirements.txt /tmp/screener_requirements.txt
RUN pip install --no-cache-dir -r /tmp/screener_requirements.txt

# Copy shared packages
COPY cemini_contracts/ /app/cemini_contracts/
COPY logit_pricing/ /app/logit_pricing/
COPY core/ /app/core/
COPY observability/ /app/observability/

# Copy service code + data
COPY opportunity_screener/ /app/opportunity_screener/
COPY data/ /app/data/

ENV PYTHONPATH=/app

EXPOSE 8003

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" || exit 1

CMD ["python3", "-m", "opportunity_screener.main"]
