from odoo import modules, models, fields, api, _
from odoo.exceptions import UserError

import ast
import logging
import threading
import json
from ..utils.asyncio_consumer import ReconnectingAsyncAttendanceConsumer
from odoo import api, SUPERUSER_ID

from ..dataclasses.datamodels import (ExchangeType, RabbitMQConsumerState,
                                      LogValues)
_logger = logging.getLogger(__name__)


RMQ_LOG = "attendance.sync.log"


class RabbitMqConsumerController(models.Model):
    CONSUMERS= {}
    THREADS = {}
    _name = 'rabbitmq.consumer.controller'
    _description = 'RabbitMQ Consumer Controller'

    name = fields.Char(string="Name", default=lambda self: _('New'))
    queue = fields.Char(string="Queue Name")
    exchange_type = fields.Selection(selection=ExchangeType.get_selection(), string="Exchange Type", default='direct')
    exchange = fields.Char(string="Exchange")
    state = fields.Selection(selection=RabbitMQConsumerState.get_selection(), string="State", default="draft")
    sync_model = fields.Many2one('ir.model', string="Sync Model", help="Select the model to sync with RabbitMQ messages.", ondelete="SET NULL")


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

    def _process_rabbitmq_message(self, channel, method, properties, body, model_name):
        _logger.info("Processing RabbitMQ message in Odoo")
        try:
            msg = json.loads(body.decode() if isinstance(body, bytes) else str(body))
        except Exception as e:
            _logger.error(f"Error decoding RabbitMQ message: {e}")
            msg = {}

        log_vals = {
            'queue_name': getattr(method, 'routing_key', None),
            'data': msg,
            'operation': (properties.headers.get('operation')) if properties.headers else None,
            'model_name': model_name
        }
        log_vals.update(self.env[RMQ_LOG].prepare_log_vals(msg))

        # Always create a new log record for every message
        registry = modules.registry.Registry.new(self.env.cr.dbname)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            try:
                log_record = env[RMQ_LOG].create(LogValues.model_validate(log_vals).__dict__)

                # Call the process_attendance_operation method if it exists
                log_record.process_odoo_operation()
                cr.commit()

            except Exception as e:
                cr.rollback()
                _logger.error(f"Error creating RabbitMQ log record: {e}")
            finally:
                cr.close()

    def action_start_consumer(self):
        global CONSUMERS ,THREADS
        queue_name = self.queue
        model_name = self.sync_model.model

        # If already running for this queue, don't start again
        if queue_name in self.CONSUMERS:
            _logger.info(f"RabbitMQ consumer for queue '{queue_name}' already running.")
            self.state = "running"
            return False

        _logger.info(f"Starting RabbitMQ consumer for queue '{queue_name}'...")

        consumer = ReconnectingAsyncAttendanceConsumer(
            exchange_name=self.exchange,
            exchange_type=self.exchange_type,
            queue_name=queue_name,
            message_callback=lambda channel, method, properties, body: self._process_rabbitmq_message(
                channel, method, properties, body, model_name
            )
        )

        thread = threading.Thread(target=consumer.run, daemon=True)
        thread.start()

        # Store consumer and thread
        self.CONSUMERS[queue_name] = consumer
        self.THREADS[queue_name] = thread

        self.state = "running"
        return True

    def action_stop_consumer(self):
        global CONSUMERS ,THREADS
        queue_name = self.queue
        consumer = self.CONSUMERS.get(queue_name)
        if consumer:
            _logger.info(f"Stopping RabbitMQ consumer for queue '{queue_name}'...")
            consumer.stop()
            self.CONSUMERS.pop(queue_name, None)
            self.THREADS.pop(queue_name, None)
            self.state = "stopped"
            return True
        else:
            _logger.warning(f"No consumer running for queue '{queue_name}'")
            return False
