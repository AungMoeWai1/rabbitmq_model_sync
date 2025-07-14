import threading
import pika
import time
import ssl
import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

# Globals
_connection = None
_channel = None
_consumer_thread = None
_stop_flag = False

# Configuration - adjust host, port, credentials as needed
RABBITMQ_HOST = "porpoise.rmq.cloudamqp.com"
RABBITMQ_PORT = 5671  # TLS port
RABBITMQ_USER = "vdejelkw"
RABBITMQ_PASSWORD = "9b1hkSWYIGOydNJsxMmYQqQZ1r9MCV0P"
QUEUE_NAME = "attendance_queue"


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
        context = ssl.create_default_context()  # TLS/SSL context

        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            virtual_host=RABBITMQ_USER,  # Use user as vhost for CloudAMQP
            credentials=credentials,
            ssl_options=pika.SSLOptions(context),
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
                # _save_sync_log(body.decode())
                _channel.basic_ack(method_frame.delivery_tag)

        if _channel.is_open:
            _channel.cancel()
        if _connection.is_open:
            _connection.close()

    except Exception as e:
        print("RabbitMQ consumer exception:", e)

# def _save_sync_log(data):
#     """Store message in attendance.sync.log inside Odoo."""
#     db_name = config.get('db_name')
#     registry = odoo.registry(db_name)  # ⚠ Replace with your actual DB name
#     with registry.cursor() as cr:
#         env = api.Environment(cr, SUPERUSER_ID, {})
#         env['attendance.sync.log'].create({
#             'queue_name': QUEUE_NAME,
#             'data': data,
#             'is_synced': False,
#         })
