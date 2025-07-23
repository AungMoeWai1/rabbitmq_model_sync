# pylint: disable=line-too-long,invalid-name,import-error,wrong-import-order,protected-access
"""Test cases for RabbitMQ Consumer Controller in Odoo"""
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase


class TestRabbitMqConsumerController(TransactionCase):
    """Test cases for RabbitMQ Consumer Controller model."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.model = self.env["ir.model"].create(
            {
                "name": "Test Model",
                "model": "test.model",
            }
        )
        self.controller = self.env["rabbitmq.consumer.controller"].create(
            {
                "name": "Test Consumer",
                "queue": "test_queue",
                "exchange_type": "direct",
                "exchange": "test_exchange",
                "sync_model": self.model.id,
            }
        )

    def test_create_consumer(self):
        """Test creating a RabbitMQ consumer controller."""
        self.assertEqual(self.controller.state, "draft")
        self.assertEqual(self.controller.queue, "test_queue")
        self.assertEqual(self.controller.exchange, "test_exchange")
        self.assertEqual(self.controller.sync_model.model, "test.model")

    @patch(
        "odoo.addons.rabbitmq_model_sync.models.rabbitmq_consumer_controller.ReconnectingAsyncAttendanceConsumer"
    )
    def test_action_start_consumer(self, mock_consumer_cls):
        """Test starting a RabbitMQ consumer."""
        mock_consumer = MagicMock()
        mock_consumer_cls.return_value = mock_consumer

        result = self.controller.action_start_consumer()
        self.assertTrue(result)
        self.assertEqual(self.controller.state, "running")
        self.assertIn("test_queue", self.controller.CONSUMERS)

    @patch(
        "odoo.addons.rabbitmq_model_sync.models.rabbitmq_consumer_controller.ReconnectingAsyncAttendanceConsumer"
    )
    def test_action_stop_consumer(self, mock_consumer_cls):
        """Test stopping a RabbitMQ consumer."""
        # Start first
        mock_consumer = MagicMock()
        mock_consumer_cls.return_value = mock_consumer
        self.controller.action_start_consumer()
        # Now stop
        result = self.controller.action_stop_consumer()
        self.assertTrue(result)
        self.assertEqual(self.controller.state, "stop")
        self.assertNotIn("test_queue", self.controller.CONSUMERS)

    @patch(
        "odoo.addons.rabbitmq_model_sync.models.rabbitmq_consumer_controller.modules.registry.Registry.new"
    )
    def test_process_rabbitmq_message(self, mock_registry_new):
        """Test processing a RabbitMQ message."""
        # Mock registry and environment
        mock_registry = MagicMock()
        mock_env = MagicMock()
        mock_log_model = MagicMock()
        mock_log_record = MagicMock()
        mock_env.__getitem__.return_value = mock_log_model
        mock_log_model.create.return_value = mock_log_record
        mock_registry.cursor.return_value.__enter__.return_value = MagicMock()
        mock_registry.cursor.return_value.__exit__.return_value = False
        mock_registry_new.return_value = mock_registry

        # Patch api.Environment to return our mock_env
        with patch("odoo.api.Environment", return_value=mock_env):
            method = MagicMock()
            method.routing_key = "test_queue"
            properties = MagicMock()
            properties.headers = {"operation": "test_op"}
            body = b'{"foo": "bar"}'
            self.controller._process_rabbitmq_message(
                method, properties, body, "test.model"
            )
            mock_log_model.create.assert_called_once()
            mock_log_record.process_odoo_operation.assert_called_once()
