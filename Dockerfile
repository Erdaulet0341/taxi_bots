FROM python:3.9-slim

WORKDIR /code

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies (this layer will be cached if requirements.txt doesn't change)
# Using BuildKit cache mount for pip cache (faster installs)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --upgrade pip && \
    pip3 install -r requirements.txt

# Copy application code
COPY . .

# Create logs directory and set permissions
RUN mkdir -p /code/logs && chmod 777 /code/logs

# Make start script executable
RUN chmod +x ./start.sh

CMD ["./start.sh"]
