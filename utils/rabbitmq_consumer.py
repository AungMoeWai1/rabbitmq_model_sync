import threading
import pika
import time

# Globals
_connection = None
_channel = None
_consumer_thread = None
_stop_flag = False

# Configuration - adjust host, port, credentials as needed
RABBITMQ_HOST = "localhost"     # Change to remote IP or hostname later
RABBITMQ_PORT = 5672            # Default AMQP port
RABBITMQ_USER = "guest"         # Default user (update in production)
RABBITMQ_PASSWORD = "guest"     # Default password
QUEUE_NAME = "attendance_queue" # Your queue name


def start_rabbitmq_consumer():
    global _consumer_thread, _stop_flag
    _stop_flag = False
    if _consumer_thread and _consumer_thread.is_alive():
        return  # Already running
    _consumer_thread = threading.Thread(target=_run_consumer, daemon=True)
    _consumer_thread.start()

def stop_rabbitmq_consumer():
    global _consumer_thread, _stop_flag
    _stop_flag = True

    if _consumer_thread and _consumer_thread.is_alive():
        _consumer_thread.join(timeout=5)  # Wait for the thread to stop
        _consumer_thread = None
        print("Consumer stopped successfully.")


def _run_consumer():
    global _connection, _channel
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=30,
            blocked_connection_timeout=300
        )

        _connection = pika.BlockingConnection(parameters)
        _channel = _connection.channel()

        _channel.queue_declare(queue=QUEUE_NAME, durable=True)

        print(f" [*] Waiting for messages in '{QUEUE_NAME}'. To exit press CTRL+C")

        for method_frame, properties, body in _channel.consume(QUEUE_NAME, inactivity_timeout=1):
            if _stop_flag:
                break
            if body:
                print("Received:", body.decode())
                _channel.basic_ack(method_frame.delivery_tag)

        if _channel.is_open:
            _channel.cancel()
        if _connection.is_open:
            _connection.close()

    except Exception as e:
        print("RabbitMQ consumer exception:", e)
