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
- **Durable queues**: Ensures message persistence across restarts
- **Error handling**: Graceful handling of connection failures and malformed messages
- **Docker support**: Containerized deployment with uv for fast dependency management

## Installation

### Prerequisites

- Access to OpenStack RabbitMQ notification system
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
   ```

3. **Deploy the application ** 

4. **Monitor**:
   - Use Coolify's built-in logging to monitor the application

### Docker Installation

For users who prefer direct Docker deployment without Coolify:

1. **Build the Docker image**:
   ```bash
   docker build -t openstack-rabbitmq-notification-to-webhook .
   ```

2. **Run with environment variables**:
   ```bash
   docker run -e RABBITMQ_USERNAME=openstack \
              -e RABBITMQ_PASSWORD=password \
              -e RABBITMQ_HOSTS=10.1.0.11:5672,10.1.0.12:5672,10.1.0.13:5672 \
              -e QUEUE_NAME=openstack-rabbitmq-notification-to-webhook \
              -e TOPIC=notifications.* \
              -e EXCHANGES=nova,neutron,openstack,heat,magnum,cinder \
              -e WEBHOOK_URL=https://your-webhook-endpoint.com/webhook \
              openstack-rabbitmq-notification-to-webhook
   ```

3. **Or run with .env file**:
   ```bash
   docker run -v $(pwd)/.env:/app/.env openstack-rabbitmq-notification-to-webhook
   ```

### Local Development Installation

For development and testing purposes only:

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd openstack-rabbitmq-notification-to-webhook
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment file**:
   ```bash
   cp env.example .env
   ```

4. **Configure environment variables** in `.env`:
   ```env
   RABBITMQ_USERNAME=openstack
   RABBITMQ_PASSWORD=your_password_here
   RABBITMQ_HOSTS=10.1.0.11:5672,10.1.0.12:5672,10.1.0.13:5672
   QUEUE_NAME=openstack-rabbitmq-notification-to-webhook
   TOPIC=notifications.*
   EXCHANGES=nova,neutron,openstack,heat,magnum,cinder
   WEBHOOK_URL=https://your-webhook-endpoint.com/webhook
   ```

5. **Run the application**:
   ```bash
   python app/openstack-rabbitmq-notification-to-webhook.py
   ```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `RABBITMQ_USERNAME` | RabbitMQ username | `openstack` |
| `RABBITMQ_PASSWORD` | RabbitMQ password | `your_password` |
| `RABBITMQ_HOSTS` | Comma-separated list of RabbitMQ hosts | `10.1.0.11:5672,10.1.0.12:5672,10.1.0.13:5672` |
| `QUEUE_NAME` | Name of the queue to consume from | `openstack-rabbitmq-notification-to-webhook` |
| `TOPIC` | Routing key pattern for notifications | `notifications.*` |
| `EXCHANGES` | Comma-separated list of OpenStack exchanges | `nova,neutron,openstack` |
| `WEBHOOK_URL` | URL to forward notifications to | `https://webhook.site/post_hook` |

### OpenStack Exchanges

The application listens to these OpenStack notification exchanges:
- **nova**: Compute instance events
- **neutron**: Network events
- **openstack**: General OpenStack events
- **heat**: Orchestration events
- **magnum**: Container orchestration events
- **cinder**: Block storage events

Adjust these accordingly

## Output Format

The application logs events in this format:
```
Event type: compute.instance.update | Project: Demo | User: user@domain.com | Instance: SERVERNAME | State: active | Description: rebooting
```

## How I use it

I use this application as part of a notification pipeline to filter OpenStack events and send relevant notifications to a Discord channel. Here's my setup:

### Architecture

```
OpenStack → RabbitMQ → openstack-rabbitmq-notification-to-webhook → n8n Webhook → Discord Channel
```

### n8n Workflow

1. **Webhook Trigger**: Receives notifications from openstack-rabbitmq-notification-to-webhook
2. **Event Filtering**: Filters events based on:
   - Event type (e.g., `compute.instance.*`, `network.port.*`)
   - Project name (specific tenants)
   - User actions (admin vs regular users)
   - Instance states (active, error, etc.)
3. **Message Formatting**: Formats filtered events for Discord
4. **Discord Integration**: Sends formatted messages to specific Discord channels

## Troubleshooting

### Common Issues

1. **Connection failures**: Check RabbitMQ credentials and host connectivity
2. **Missing environment variables**: Ensure all required variables are set in `.env`
3. **Webhook failures**: Verify webhook URL is accessible and accepts POST requests. With n8n, make sure your workflow is Active
4. **Permission errors**: Ensure RabbitMQ user has appropriate permissions

### Debug Mode

To see full notification payloads, uncomment this line in `app/openstack-rabbitmq-notification-to-webhook.py`:
```python
print(f"Received notification: {json.dumps(notification, indent=2)}")
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is a permissive license that allows for:
- Commercial use
- Modification
- Distribution
- Private use
- Sublicensing

The only requirement is that the original license and copyright notice be included in any substantial portions of the software. 