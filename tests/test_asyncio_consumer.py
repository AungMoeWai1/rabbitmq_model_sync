"""Test cases for the AsyncAttendanceConsumer and ReconnectingAsyncAttendanceConsumer classes."""
import unittest
from unittest.mock import MagicMock, patch

from odoo.addons.rabbitmq_model_sync.utils.asyncio_consumer import (AsyncAttendanceConsumer, ReconnectingAsyncAttendanceConsumer) # pylint: disable=line-too-long,import-error


class TestAsyncAttendanceConsumer(unittest.TestCase):
    """Test cases for AsyncAttendanceConsumer."""

    def setUp(self):
        self.exchange_name = ""
        self.exchange_type = "direct"
        self.queue_name = "test_queue"
        self.callback = MagicMock()

    @patch("odoo.addons.rabbitmq_model_sync.utils.asyncio_consumer.AsyncioConnection")
    def test_connect(self, mock_connection):
        """Test connection establishment."""
        consumer = AsyncAttendanceConsumer(
            self.exchange_name, self.exchange_type, self.queue_name, self.callback
        )
        consumer.connect()
        mock_connection.assert_called_once()

    @patch(
        "odoo.addons.rabbitmq_model_sync.utils.asyncio_consumer.AsyncioConnection",
        side_effect=Exception("Simulated connection failure"),
    )
    def test_connect_failure(self, _):
        """Test connection failure handling."""
        consumer = AsyncAttendanceConsumer(
            self.exchange_name, self.exchange_type, self.queue_name, self.callback
        )

        with self.assertRaises(Exception) as context:
            consumer.connect()

        self.assertIn("success", str(context.exception))

    def test_on_message_ack(self):
        """Test message acknowledgment."""
        consumer = AsyncAttendanceConsumer(
            self.exchange_name, self.exchange_type, self.queue_name, self.callback
        )

        channel = MagicMock()
        method = MagicMock()
        method.delivery_tag = 123
        props = MagicMock()
        body = b'{"example": "data"}'

        consumer.on_message(channel, method, props, body)
        channel.basic_ack.assert_called_once_with(123)
        self.callback.assert_called_once()

    def test_on_message_callback_failure(self):
        """Test message acknowledgment on callback failure."""
        consumer = AsyncAttendanceConsumer(
            self.exchange_name, self.exchange_type, self.queue_name, self.callback
        )

        # Callback will raise an error
        self.callback.side_effect = Exception("Callback crash")

        channel = MagicMock()
        method = MagicMock()
        method.delivery_tag = 456
        props = MagicMock()
        body = b'{"data": "fail"}'

        # Should still acknowledge the message even if callback crashes
        consumer.on_message(channel, method, props, body)

        channel.basic_ack.assert_called_once_with(456)
        self.callback.assert_called_once()


class TestReconnectingAsyncConsumer(unittest.TestCase):
    """Test cases for ReconnectingAsyncAttendanceConsumer."""

    def setUp(self):
        self.exchange_name = ""
        self.exchange_type = "direct"
        self.queue_name = "test_queue"
        self.callback = MagicMock()

    @patch(
        "odoo.addons.rabbitmq_model_sync.utils.asyncio_consumer.AsyncAttendanceConsumer.start"
    )
    @patch(
        "odoo.addons.rabbitmq_model_sync.utils.asyncio_consumer.AsyncAttendanceConsumer.stop"
    )
    def test_reconnect_logic(self, mock_stop, _):
        """Test reconnect logic of ReconnectingAsyncAttendanceConsumer."""
        reconnecting_consumer = ReconnectingAsyncAttendanceConsumer(
            self.exchange_name, self.exchange_type, self.queue_name, self.callback
        )
        reconnecting_consumer._consumer.should_reconnect = True # pylint: disable=protected-access
        reconnecting_consumer._consumer.was_consuming = False # pylint: disable=protected-access
        reconnecting_consumer._running = False # pylint: disable=protected-access

        reconnecting_consumer._maybe_reconnect() # pylint: disable=protected-access
        mock_stop.assert_called_once()

    def test_reconnect_delay(self):
        """Test the reconnect delay logic."""
        consumer = ReconnectingAsyncAttendanceConsumer(
            self.exchange_name, self.exchange_type, self.queue_name, self.callback
        )
        self.assertEqual(consumer._get_reconnect_delay(), 1) # pylint: disable=protected-access
        self.assertEqual(consumer._get_reconnect_delay(), 2) # pylint: disable=protected-access

        consumer._consumer.was_consuming = True # pylint: disable=protected-access
        self.assertEqual(consumer._get_reconnect_delay(), 0) # pylint: disable=protected-access
