FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install build dependencies and pip requirements
COPY requirements.txt ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y build-essential gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Default port used by the container. docker-compose can override this via command.
ENV BACKEND_PORT=8000

# Default command; docker-compose will typically override the port via the command entry
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
