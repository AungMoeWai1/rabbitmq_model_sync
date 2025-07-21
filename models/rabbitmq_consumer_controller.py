#-*- coding: utf-8 -*-
import json
import logging
import threading

from psycopg2 import DatabaseError

from odoo import SUPERUSER_ID, _, api, fields, models, modules

from ..dataclasses.datamodels import (ExchangeType, LogValues,
                                      RabbitMQConsumerState)
from ..utils.asyncio_consumer import ReconnectingAsyncAttendanceConsumer

_logger = logging.getLogger(__name__)


RMQ_LOG = "rabbitmq.log"

class RabbitMqConsumerController(models.Model):
    CONSUMERS = {}
    THREADS = {}
    _name = "rabbitmq.consumer.controller"
    _description = "RabbitMQ Consumer Controller"

    name = fields.Char(string="Name", default=lambda self: _("New"))
    queue = fields.Char(string="Queue Name")
    exchange_type = fields.Selection(
        selection=ExchangeType.get_selection(), string="Exchange Type", default="direct"
    )
    exchange = fields.Char(string="Exchange")
    state = fields.Selection(
        selection=RabbitMQConsumerState.get_selection(), string="State", default="draft"
    )
    sync_model = fields.Many2one(
        "ir.model",
        string="Sync Model",
        help="Select the model to sync with RabbitMQ messages.",
        ondelete="SET NULL",
    )

    @api.model_create_multi
    def create(self, vals):
        """Override create method to set default name."""
        for val in vals:
            if val.get("name", "New") == "New":
                val["name"] = (
                    self.env["ir.sequence"].next_by_code("rabbitmq.control.code")
                    or "New"
                )
        return super().create(vals)

    def _process_rabbitmq_message(self, method, properties, body, model_name):
        _logger.info("Processing RabbitMQ message in Odoo")
        try:
            msg = json.loads(body.decode() if isinstance(body, bytes) else str(body))
        except UnicodeDecodeError as e:
            _logger.error("Error decoding RabbitMQ message: %s", e)
            msg = {}

        log_vals = {
            "queue_name": getattr(method, "routing_key", None),
            "data": msg,
            "operation": (
                (properties.headers.get("operation")) if properties.headers else None
            ),
            "model_name": model_name,
        }
        log_vals.update(self.env[RMQ_LOG].prepare_log_vals(msg))

        # Always create a new log record for every message
        registry = modules.registry.Registry.new(self.env.cr.dbname)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            try:
                log_record = env[RMQ_LOG].create(
                    LogValues.model_validate(log_vals).__dict__
                )

                # Call the process_attendance_operation method if it exists
                log_record.process_odoo_operation()
                cr.commit()

            except DatabaseError as e:
                cr.rollback()
                _logger.error("Error creating RabbitMQ log record: %s", e)
            finally:
                cr.close()

    def action_start_consumer(self):
        """Start the RabbitMQ consumer for this controller."""
        queue_name = self.queue
        model_name = self.sync_model.model

        # If already running for this queue, don't start again
        if queue_name in self.CONSUMERS:
            _logger.info("RabbitMQ consumer for queue '%s' already running.", queue_name)
            self.state = "running"
            return False

        _logger.info("Starting RabbitMQ consumer for queue '%s'...", queue_name)

        consumer = ReconnectingAsyncAttendanceConsumer(
            exchange_name=self.exchange,
            exchange_type=self.exchange_type,
            queue_name=queue_name,
            message_callback=lambda method, properties, body: self._process_rabbitmq_message(
                method, properties, body, model_name
            ),
        )

        thread = threading.Thread(target=consumer.run, daemon=True)
        thread.start()

        # Store consumer and thread
        self.CONSUMERS[queue_name] = consumer
        self.THREADS[queue_name] = thread

        self.state = "running"
        return True

    def action_stop_consumer(self):
        """Stop the RabbitMQ consumer for this controller."""
        queue_name = self.queue
        consumer = self.CONSUMERS.get(queue_name)
        if consumer:
            _logger.info("Stopping RabbitMQ consumer for queue '%s'...", queue_name)
            consumer.stop()
            self.CONSUMERS.pop(queue_name, None)
            self.THREADS.pop(queue_name, None)
            self.state = "stop"
            return True
        _logger.warning("No consumer running for queue '%s'", queue_name)
        return False
