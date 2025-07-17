"""RabbitMQ Consumer for Attendance Sync
This module connects to a RabbitMQ server to consume messages related to attendance sync.
It processes messages, extracts relevant data, and saves it to the Odoo database.
It also handles TLS/SSL connections and uses threading for asynchronous message consumption.
"""
import json
import os
import ssl
import threading
from datetime import datetime

import pika
from odoo import api, fields
from odoo.modules.registry import Registry

from . import credential_reader as cr

# Globals
_CONNECTION = None
_CHANNEL = None
_CONSUMER_THREAD = None
_STOP_FLAG = False

# Configuration - adjust host, port, credentials as needed
# RABBITMQ_HOST = "porpoise.rmq.cloudamqp.com"
# RABBITMQ_PORT = 5671  # TLS port
# RABBITMQ_USER = "vdejelkw"
# RABBITMQ_PASSWORD = "9b1hkSWYIGOydNJsxMmYQqQZ1r9MCV0P"
# QUEUE_NAME = "attendance_queue"

os.getcwd()

RABBITMQ_CONFIG = cr.load_rabbitmq_config(
    "/home/aungmoewai/amw/project/odoo/odoo18/custom_addon/rabbitmq_attendance_sync/rabbitmq_credential.env"
)

RABBITMQ_HOST = RABBITMQ_CONFIG["host"]
RABBITMQ_PORT = RABBITMQ_CONFIG["port"]
RABBITMQ_USER = RABBITMQ_CONFIG["user"]
RABBITMQ_PASSWORD = RABBITMQ_CONFIG["password"]
QUEUE_NAME = RABBITMQ_CONFIG["queue"]


def start_rabbitmq_consumer():
    """Start the RabbitMQ consumer thread."""
    global _CONSUMER_THREAD, _STOP_FLAG
    _STOP_FLAG = False
    if _CONSUMER_THREAD and _CONSUMER_THREAD.is_alive():
        return  # Already running
    _CONSUMER_THREAD = threading.Thread(target=_run_consumer, daemon=True)
    _CONSUMER_THREAD.start()


def stop_rabbitmq_consumer():
    """Stop the RabbitMQ consumer thread."""
    global _CONSUMER_THREAD, _STOP_FLAG
    _STOP_FLAG = True

    if _CONSUMER_THREAD and _CONSUMER_THREAD.is_alive():
        _CONSUMER_THREAD.join(timeout=5)  # Wait for the thread to stop
        _CONSUMER_THREAD = None
        print("Consumer stopped successfully.")


def _run_consumer():
    global _CONNECTION, _CHANNEL
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
            blocked_connection_timeout=300,
        )

        _CONNECTION = pika.BlockingConnection(parameters)
        _CHANNEL = _CONNECTION.channel()

        _CHANNEL.queue_declare(queue=QUEUE_NAME, durable=True)

        print(f" [*] Waiting for messages in '{QUEUE_NAME}'. To exit press CTRL+C")

        for method_frame, properties, body in _CHANNEL.consume(
            QUEUE_NAME, inactivity_timeout=1
        ):
            if _STOP_FLAG:
                break
            if body:
                try:
                    message_data = json.loads(body.decode())
                except json.JSONDecodeError as e:
                    print("Invalid JSON message received:", e)
                    _CHANNEL.basic_ack(method_frame.delivery_tag)
                    continue

                # Read custom header from message
                check_type = None
                if properties.headers and "type" in properties.headers:
                    check_type = properties.headers[
                        "type"
                    ]  # Expected: 'check_in' or 'check_out'

                print(f"Received message: {message_data}")
                print(f"Type from header: {check_type}")

                # Example fields extraction:
                employee_id = message_data.get("employee_id")
                timestamp = message_data.get("time")
                parsed_date = (
                datetime.strptime(timestamp, "%m/%d/%Y %H:%M:%S")
                if timestamp
                else fields.Datetime.now()
            )

                print(
                    f"Employee ID: {employee_id} | Time: {parsed_date} | Action: {check_type}"
                )

                # Optional: Save to Odoo DB via _save_sync_log()
                _save_sync_log(employee_id, parsed_date, check_type, message_data)

                _CHANNEL.basic_ack(method_frame.delivery_tag)

        if _CHANNEL.is_open:
            _CHANNEL.cancel()
        if _CONNECTION.is_open:
            _CONNECTION.close()

    except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelError) as e:
        print("RabbitMQ connection/channel error:", e)
    except json.JSONDecodeError as e:
        print("Invalid JSON message received:", e)
    except ValueError as e:
        print("Value error:", e)
    except KeyError as e:
        print("Key error:", e)


def _save_sync_log(employee_id, timestamp, check_type, message_data):
    try:
        # db_name = config.get('db_name')
        with Registry("dinger").cursor() as cursor:
            env = api.Environment(cursor, api.SUPERUSER_ID, {})

            log_record = env["attendance.sync.log"].create(
                {
                    "employee_id": employee_id,
                    "queue_name": QUEUE_NAME,
                    "data": message_data,
                    "type": check_type or "check_in",
                    "date": timestamp,
                    "state": "new",
                }
            )
            cursor.commit()
            log_record.action_retry_sync()
            print(f"[+] Log saved for employee ID {employee_id}")

    except (ValueError, KeyError, TypeError) as e:
        print("Error saving sync log:", e)
