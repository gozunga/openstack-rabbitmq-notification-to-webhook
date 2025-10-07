import pika
import requests
import json
import sys
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Load environment variables from .env file
load_dotenv()

def get_required_env_var(var_name):
    """Get a required environment variable or exit if not found."""
    value = os.getenv(var_name)
    if value is None or value.strip() == '':
        print(f"Error: Required environment variable '{var_name}' is not set.")
        sys.exit(1)
    return value

def get_optional_env_var(var_name):
    """Get an optional environment variable."""
    value = os.getenv(var_name)
    return value if value is not None else []

# Configuration from environment variables - no defaults, fail if missing
RABBITMQ_USERNAME = get_required_env_var('RABBITMQ_USERNAME')
RABBITMQ_PASSWORD = get_required_env_var('RABBITMQ_PASSWORD')
RABBITMQ_HOSTS = get_required_env_var('RABBITMQ_HOSTS').split(',')
QUEUE_NAME = get_required_env_var('QUEUE_NAME')
TOPIC = get_required_env_var('TOPIC')
EXCHANGES = get_required_env_var('EXCHANGES').split(',')
WEBHOOK_URL = get_required_env_var('WEBHOOK_URL')

# Optional configuration
IGNORED_EVENT_TYPES = get_optional_env_var('IGNORED_EVENT_TYPES').split(',')

# Timezone configuration
TZ_NAME = get_optional_env_var('TZ') or 'UTC'

def log_with_timestamp(message):
    """Log a message with timestamp in the configured timezone."""
    try:
        tz = pytz.timezone(TZ_NAME)
        timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback to UTC if timezone is invalid
        timestamp = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()  # Force flush to ensure logs appear in Docker containers

def setup_connection():
    """
    Establish a connection to RabbitMQ, trying multiple hosts for failover.
    """
    for host in RABBITMQ_HOSTS:
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
            parameters = pika.ConnectionParameters(
                host=host.split(':')[0],
                port=int(host.split(':')[1]),
                credentials=credentials,
                heartbeat=600,  # Adjust as needed for long-running connections
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(parameters)
            log_with_timestamp(f"Connected to RabbitMQ at {host}")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            log_with_timestamp(f"Failed to connect to {host}: {e}")
    raise Exception("Could not connect to any RabbitMQ host")

def setup_channel(channel):
    """
    Declare a quorum queue and bind it to the specified exchanges with the topic.
    Assumes exchanges are topic-type, as per OpenStack notifications.
    """
    # Declare a quorum queue with specific arguments
    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments={
            'x-queue-type': 'quorum',
            'x-delivery-limit': 10,  # Optional: limits redelivery attempts
            'x-dead-letter-exchange': '',  # Optional: specify if DLX is needed
            'x-dead-letter-routing-key': f"{QUEUE_NAME}.dlq"  # Optional: DLQ routing key
        }
    )

    for exchange in EXCHANGES:
        # Declare exchange if not exists (topic type for OpenStack notifications)
        channel.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)

        # Bind queue to exchange with routing key
        channel.queue_bind(exchange=exchange, queue=QUEUE_NAME, routing_key=TOPIC)
        log_with_timestamp(f"Bound quorum queue '{QUEUE_NAME}' to exchange '{exchange}' with routing key '{TOPIC}'")

def callback(ch, method, properties, body):
    """
    Callback function for consumed messages.
    Sends the notification payload as JSON to the webhook URL.
    """
    try:
        # Assume body is JSON-encoded (as in OpenStack notifications)
        notification = json.loads(body)

        # Display only the event_type
        oslo_message = notification.get('oslo.message', '{}')
        if isinstance(oslo_message, str):
            try:
                oslo_message = json.loads(oslo_message)
            except json.JSONDecodeError:
                oslo_message = {}
        event_type = oslo_message.get('event_type', 'unknown')

        # Check if this event type should be ignored
        if event_type in IGNORED_EVENT_TYPES:
            log_with_timestamp(f"Ignoring event type: {event_type}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Extract additional context information
        context_project_name = oslo_message.get('_context_project_name', 'unknown')
        context_user_name = oslo_message.get('_context_user_name', 'unknown')
        
        # Extract display_name from payload if it exists
        display_name = 'unknown'
        state = 'unknown'
        state_description = 'unknown'
        payload = oslo_message.get('payload', {})
        if payload:
            display_name = payload.get('display_name', 'unknown')
            state = payload.get('state', 'unknown')
            state_description = payload.get('state_description', 'unknown')

        log_with_timestamp(f"Event type: {event_type} | Project: {context_project_name} | User: {context_user_name} | Instance: {display_name} | State: {state} | Description: {state_description}")

        # Send as JSON blob via POST
        response = requests.post(WEBHOOK_URL, json=notification)
        response.raise_for_status()  # Raise error on bad status

        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError as e:
        log_with_timestamp(f"Invalid JSON in message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except requests.RequestException as e:
        log_with_timestamp(f"Failed to send to webhook: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)  # Discard on failure
    except Exception as e:
        log_with_timestamp(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    connection = setup_connection()
    channel = connection.channel()

    setup_channel(channel)

    # Consume from the queue
    channel.basic_qos(prefetch_count=1)  # Process one message at a time
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    log_with_timestamp(f"Listening for notifications on quorum queue '{QUEUE_NAME}'...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        log_with_timestamp("Interrupted, closing connection...")
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()
