# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies using uv
RUN uv --system pip install -r requirements.txt

# Copy application code
COPY app/ ./app/

# Run the application
CMD ["python", "app/openstack-rabbitmq-notification-to-webhook.py"]
