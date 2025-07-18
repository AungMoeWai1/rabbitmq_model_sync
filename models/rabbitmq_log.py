#-*- utf-8 -*-
from datetime import datetime
from odoo import fields, models
from ..dataclasses.datamodels import OperationType, RecordStatus

date_list = ['check_in', 'check_out']

def firebase_iso_to_odoo_datetime(iso_str):
    # Convert to datetime object (UTC)
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    # Convert to Odoo string format
    return fields.Datetime.to_string(dt)

class RabibitLog(models.Model):
    _name = "rabbitmq.log"

    queue_name = fields.Char(string="Queue Name")
    data = fields.Json(
        string="Data",
        help="Message received from RabbitMQ")
    state=fields.Selection(selection=RecordStatus.get_selection(),string="Status",default='new')
    operation = fields.Selection(selection=OperationType.get_selection(), string="Operation", help="Type of operation (check-in/check-out)")
    model_name = fields.Char(string="Model Name", help="Name of the model associated with this log entry")
    record_id = fields.Many2oneReference(model_field='model_name', string="Record ID", help="Reference to the record in the model")

    def prepare_log_vals(self, msg):
        """Prepare log values from message dict."""
        vals = {}
        if 'record_id' in msg:
            vals['record_id'] = msg['record_id']
        return vals


    def action_retry_sync(self):
        """Retry the sync operation for this log entry."""
        self.state = 'success'

    def _prepare_vals(self, vals):
        """Convert datetime for check_in/check_out if present."""
        return {k: firebase_iso_to_odoo_datetime(v) if k in date_list else v for k, v in vals.items()}

    def _execute_operation(self, operation, vals):
        """Handle create/write operation generically."""
        try:
            vals = self._prepare_vals(vals)
            record_id = vals.pop('record_id', None)

            if operation == 'create':
                rec = self.env[self.model_name].create(vals)
                self.record_id = rec.id
                self.state = 'success'
                return rec

            elif operation == 'write' and record_id:
                record = self.env[self.model_name].browse(record_id)
                if record.exists() and record.write(vals):
                    self.record_id = record.id
                    self.state = 'success'
                    return True

            self.state = 'fail'
            return False

        except Exception as e:
            self.state = 'fail'
            print(f"Error at {operation}:", e)
            return False

    def process_odoo_operation(self):
        """Process attendance operation based on log record's operation type."""
        if self.operation in ['create', 'write']:
            return self._execute_operation(self.operation, self.data)
        self.state = 'fail'
        return False
