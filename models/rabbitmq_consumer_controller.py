"""This file is the controller for the RabbitMQ Consumer."""
from odoo import _, api, fields, models # pylint: disable=import-error

from ..utils import rabbitmq_consumer

CONSUMER_STATE = [("draft", "Draft"), ("stop", "Stop"), ("running", "Running")]
EXCHANGE_TYPE = [
    ("direct", "Direct"),
    ("topic", "Topic"),
    ("fanout", "Fanout"),
    ("header", "Header"),
]


class RabbitMqConsumerController(models.Model):
    """Controller for RabbitMQ Consumer operations."""
    _name = "rabbitmq.consumer.controller"
    _description = "RabbitMQ Consumer Controller"

    name = fields.Char(
        string="Name",
        default=lambda self: _("New"),
    )
    queue = fields.Char(string="Queue Name")
    exchange_type = fields.Selection(
        EXCHANGE_TYPE, string="Exchange Type", default="direct"
    )
    exchange = fields.Char(string="Exchange")
    state = fields.Selection(CONSUMER_STATE, string="State", default="draft")

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

    def action_start_consumer(self):
        """Start the RabbitMQ consumer."""
        rabbitmq_consumer.start_rabbitmq_consumer()
        self.state = "running"
        return True

    def action_stop_consumer(self):
        """Stop the RabbitMQ consumer"""
        rabbitmq_consumer.stop_rabbitmq_consumer()
        self.state = "stop"
        return True
