import threading
import pika
import time
import json
import ssl
import odoo
import os
from . import credential_reader as cr
from odoo import api, SUPERUSER_ID
from odoo.tools import config
from datetime import datetime
from odoo import fields
from odoo.modules.registry import Registry

# Globals
_connection = None
_channel = None
_consumer_thread = None
_stop_flag = False

# Configuration - adjust host, port, credentials as needed
# RABBITMQ_HOST = "porpoise.rmq.cloudamqp.com"
# RABBITMQ_PORT = 5671  # TLS port
# RABBITMQ_USER = "vdejelkw"
# RABBITMQ_PASSWORD = "9b1hkSWYIGOydNJsxMmYQqQZ1r9MCV0P"
# QUEUE_NAME = "attendance_queue"

os.getcwd()

RABBITMQ_CONFIG = cr.load_rabbitmq_config(
    '/home/aungmoewai/amw/project/odoo/odoo18/custom_addon/rabbitmq_attendance_sync/rabbitmq_credential.env')

RABBITMQ_HOST = RABBITMQ_CONFIG['host']
RABBITMQ_PORT = RABBITMQ_CONFIG['port']
RABBITMQ_USER = RABBITMQ_CONFIG['user']
RABBITMQ_PASSWORD = RABBITMQ_CONFIG['password']
QUEUE_NAME = RABBITMQ_CONFIG['queue']


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
                try:
                    message_data = json.loads(body.decode())
                except Exception as e:
                    print("Invalid JSON message received:", e)
                    _channel.basic_ack(method_frame.delivery_tag)
                    continue

                # Read custom header from message
                check_type = None
                if properties.headers and 'type' in properties.headers:
                    check_type = properties.headers['type']  # Expected: 'check_in' or 'check_out'

                print(f"Received message: {message_data}")
                print(f"Type from header: {check_type}")

                # Example fields extraction:
                employee_id = message_data.get('employee_id')
                timestamp = message_data.get('time')

                print(f"Employee ID: {employee_id} | Time: {timestamp} | Action: {check_type}")

                # Optional: Save to Odoo DB via _save_sync_log()
                _save_sync_log(employee_id, timestamp, check_type, message_data)

                _channel.basic_ack(method_frame.delivery_tag)

        if _channel.is_open:
            _channel.cancel()
        if _connection.is_open:
            _connection.close()

    except Exception as e:
        print("RabbitMQ consumer exception:", e)


def _save_sync_log(employee_id, timestamp, check_type, message_data):
    try:
        # db_name = config.get('db_name')
        with Registry("dinger").cursor() as cr:
            env = api.Environment(cr, odoo.SUPERUSER_ID, {})

            date_str = message_data.get('time')  # Example: "07/16/2025 19:00:00"
            # Convert to datetime object (assuming format MM/DD/YYYY HH:MM:SS)
            parsed_date = datetime.strptime(date_str, "%m/%d/%Y %H:%M:%S") if date_str else fields.Datetime.now()

            log_record=env['attendance.sync.log'].create({
                'employee_id': employee_id,
                'queue_name': QUEUE_NAME,
                'data': message_data,
                'type': check_type or 'check_in',
                'date':parsed_date,
                'state': 'new',
            })
            cr.commit()
            log_record.action_retry_sync()
            print(f"[+] Log saved for employee ID {employee_id}")

    except Exception as e:
        print("Error saving sync log:", e)
