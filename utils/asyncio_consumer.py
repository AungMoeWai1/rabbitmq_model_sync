import asyncio
import logging
import os
# import ssl
import time
from pathlib import Path

import pika
from dotenv import dotenv_values
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.exceptions import (AMQPChannelError, AMQPConnectionError,
                             ChannelClosedByBroker)
from pika.exchange_type import ExchangeType

DEFAULT_FILE_NAME = ".env"
DEFAULT_DIR = "rabbitmq_model_sync"


def get_file_path(file_name=DEFAULT_FILE_NAME):
    """Get default file path

    Args:
        file_name (str, optional): Name of the firebase key file. Defaults to DEFAULT_FILE_NAME.

    Returns:
        None
    """
    path = Path(os.path.dirname(__file__))
    return os.path.join(path.parent.parent.absolute(), DEFAULT_DIR, file_name)


def get_rabbitmq_config(file_name=DEFAULT_FILE_NAME):
    """Get RabbitMQ configuration from .env file."""
    config_path = get_file_path(file_name)
    return dotenv_values(config_path)

LOGGER = logging.getLogger(__name__)

# pylint: disable=too-many-instance-attributes,too-many-arguments
class AsyncAttendanceConsumer:
    RABBITMQ_CONFIG = get_rabbitmq_config()
    EXCHANGE = ""
    EXCHANGE_TYPE = ExchangeType.direct
    # QUEUE = QUEUE_NAME
    ROUTING_KEY = RABBITMQ_CONFIG["queue"]

    def __init__(self, exchange_name, exchange_type, queue_name, message_callback=None):
        self.message_callback = message_callback
        self._queue = queue_name
        self._exchange_name = exchange_name
        self._exchange_type = exchange_type
        self._connection = None
        self._channel = None
        self._closing = False
        self._consuming = False
        self.should_reconnect = False
        self.was_consuming = False

    def connect(self):
        """Connect to RabbitMQ server."""
        credentials = pika.PlainCredentials(
            self.RABBITMQ_CONFIG["user"], self.RABBITMQ_CONFIG["password"]
        )
        # context = ssl.create_default_context()
        parameters = pika.ConnectionParameters(
            host=self.RABBITMQ_CONFIG["host"],
            port=self.RABBITMQ_CONFIG["port"],
            virtual_host="/",
            credentials=credentials,
            # ssl_options=pika.SSLOptions(context),
            heartbeat=30,
            blocked_connection_timeout=300,
        )
        LOGGER.info("Connecting to RabbitMQ...")
        return AsyncioConnection(
            parameters=parameters,
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed,
        )

    def on_connection_open(self, connection):
        """Open a channel when the connection is opened."""
        LOGGER.info("Connection opened")
        self._connection = connection
        self.open_channel()

    def on_connection_open_error(self, _, error):
        """Stop the consumer if connection open fails."""
        LOGGER.error("Connection open failed: %s", error)
        self.should_reconnect = True
        self.stop()

    def on_connection_closed(self, _, reason):
        """Close the channel and stop consuming when the connection is closed."""
        LOGGER.warning("Connection closed: %s", reason)
        self._channel = None
        if not self._closing:
            self.should_reconnect = True
            self.stop()

    def open_channel(self):
        """Open a channel for the connection."""
        LOGGER.info("Opening channel...")
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """Callback when the channel is opened."""
        LOGGER.info("Channel opened")
        self._channel = channel
        self.setup_queue(self._queue)

    def setup_queue(self, queue_name):
        """Declare the queue and bind it to the exchange."""
        LOGGER.info("Declaring queue: %s", queue_name)
        self._channel.queue_declare(
            queue=queue_name, durable=True, callback=self.on_queue_declareok
        )

    def on_queue_declareok(self, _):
        """Start consuming with declared queue"""
        LOGGER.info("Queue declared, starting to consume...")
        self.start_consuming()

    def start_consuming(self):
        """Start consuming from provided queue"""
        if not self._consuming:
            self._channel.basic_consume(
                queue=self._queue, on_message_callback=self.on_message
            )
            self.was_consuming = True
            self._consuming = True
            LOGGER.info("Started consuming")

    def stop_consuming(self):
        """Stop consuming messages from the queue."""
        if self._consuming and self._channel:
            LOGGER.info("Stopping consuming")
            self._channel.close()
            self._consuming = False

    def on_message(self, channel, method, properties, body):
        """Received queue message callback."""
        LOGGER.info("Received message: %s", body.decode())
        # Pass all message info to the callback
        if self.message_callback:
            self.message_callback(method, properties, body)
        channel.basic_ack(method.delivery_tag)

    def stop(self):
        """Stop the consumer."""
        if not self._closing:
            self._closing = True
            LOGGER.info("Stopping")
            self.stop_consuming()
            if self._connection:
                self._connection.ioloop.stop()
            LOGGER.info("Stopped")

    def start(self):
        """Start the consumer."""
        self._closing = False
        self.should_reconnect = False
        self.was_consuming = False
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._connection = self.connect()
        loop.run_forever()


class ReconnectingAsyncAttendanceConsumer:
    def __init__(self, exchange_name, exchange_type, queue_name, message_callback=None):
        self._reconnect_delay = 0
        self._consumer = AsyncAttendanceConsumer(
            exchange_name, exchange_type, queue_name, message_callback
        )
        self._running = False

    def run(self):
        """Run the consumer in a loop, reconnecting on failure."""
        self._running = True
        while self._running:
            try:
                self._consumer.start()
            except (AMQPConnectionError, ChannelClosedByBroker, AMQPChannelError) as e:
                LOGGER.error("Pika exception: %s", e)
                self._consumer.should_reconnect = True
            self._maybe_reconnect()

    def stop(self):
        """Stop the consumer."""
        self._running = False
        self._consumer.stop()

    def start_consuming(self):
        """Start consuming messages from the queue."""
        self._consumer.start_consuming()

    def stop_consuming(self):
        """Stop consuming messages from the queue."""
        self._consumer.stop_consuming()

    def _maybe_reconnect(self):
        """Reconnect if the consumer indicates it should."""
        if self._consumer.should_reconnect:
            self._consumer.stop()
            reconnect_delay = self._get_reconnect_delay()
            LOGGER.info("Reconnecting after %d seconds", reconnect_delay)
            time.sleep(reconnect_delay)
            self._consumer = AsyncAttendanceConsumer(
                exchange_name=self._consumer._exchange_name,
                exchange_type=self._consumer._exchange_type,
                queue_name=self._consumer._queue,
                message_callback=self._consumer.message_callback,
            )

    def _get_reconnect_delay(self):
        """Calculate the delay before the next reconnection attempt."""
        if self._consumer.was_consuming:
            self._reconnect_delay = 0
        else:
            self._reconnect_delay += 1
        self._reconnect_delay = min(self._reconnect_delay, 30)
        return self._reconnect_delay
