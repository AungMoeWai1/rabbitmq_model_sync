
from odoo import fields, models

class AttendanceSyncLog(models.Model):
    _name = "attendance.sync.log"

    queue_name = fields.Char(string="Queue Name")
    data = fields.Json()
    is_synced = fields.Boolean(string="Is Synced",default=False)
    attendance_id = fields.Many2one(comodel_name='hr.attendance',string="Attendance ID")