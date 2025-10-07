# OpenStack Notification Forwarder
A Python application that consumes OpenStack notifications from RabbitMQ and forwards them to webhooks. This tool acts as a bridge between OpenStack's notification system and external services that accept webhooks, like n8n workflows, zapier tasks, or your own tools.

## What it does
This application:
1. **Connects to RabbitMQ**: Establishes connections to OpenStack's RabbitMQ notification system
2. **Consumes notifications**: Listens for OpenStack events across multiple exchanges (nova, neutron, openstack, heat, magnum, cinder)
3. **Parses OpenStack notifications**: Extracts event information from the `oslo.message` format
4. **Forwards to webhooks**: Sends the complete notification payload to a configured webhook URL
5. **Provides logging**: Displays event information including event type, project, user, instance name, and state

## Features
- **Failover support**: Connects to multiple RabbitMQ hosts for high availability
- **Environment-based configuration**: Uses `.env` files for secure configuration management
- **Durable quorum queues**: Uses RabbitMQ quorum queues for enhanced reliability, fault tolerance, and message persistence across restarts
- **Error handling**: Graceful handling of connection failures and malformed messages
- **Docker support**: Containerized deployment with uv for fast dependency management

## Installation
### Prerequisites
- Access to OpenStack RabbitMQ notification system (RabbitMQ 3.8 or higher required for quorum queues)
- Webhook endpoint to receive notifications
- Coolify instance (recommended) or Docker environment

### Coolify Installation (Recommended)
[Coolify](https://coolify.io) is the recommended deployment method for production use. It provides easy management, monitoring, and scaling capabilities. [Gozunga](https://gozunga.com) is a proud sponsor of Coolify.

1. **Add to Coolify**:
   - In your Coolify dashboard, click "New Resource" → "Application"
   - Select "Docker Image" as the source
   - Use the GitHub repository URL or build from source
2. **Configure Environment Variables**:
   Set these required environment variables in your Coolify application settings:
   ```env
   RABBITMQ_USERNAME=openstack
   RABBITMQ_PASSWORD=your_rabbitmq_password
   RABBITMQ_HOSTS=10.1.0.11:5672,10.1.0.12:5672,10.1.0.13:5672
   QUEUE_NAME=openstack-rabbitmq-notification-to-webhook
   TOPIC=notifications.*
   EXCHANGES=nova,neutron,openstack,heat,magnum,cinder
   WEBHOOK_URL=https://your-webhook-endpoint.com/webhook
