# Use Python 3.11 slim image
FROM python:3.11-slim

# Set timezone
ENV TZ=UTC
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies using uv
RUN uv pip install -r requirements.txt --system 

# Copy application code
COPY app/ ./app/

# Run the application with unbuffered output
CMD ["python", "-u", "app/openstack-rabbitmq-notification-to-webhook.py"]
