FROM python:3.11-slim

WORKDIR /app

# Install system deps for psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY cemini_mcp/requirements.txt /tmp/mcp_requirements.txt
RUN pip install --no-cache-dir -r /tmp/mcp_requirements.txt

# Copy shared packages and service code
COPY cemini_contracts/ /app/cemini_contracts/
COPY cemini_mcp/ /app/cemini_mcp/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8002

CMD ["python", "-m", "cemini_mcp.server"]
