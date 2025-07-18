from odoo import fields, models

class AttendanceSyncLog(models.Model):
    _name = "attendance.sync.log"
    _inherit = "rabbitmq.log"
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(comodel_name='hr.employee', string="Employee ID")
    attendance_id = fields.Many2one(comodel_name='hr.attendance', string="Attendance ID")

    def action_create(self, vals={}):
        return self._execute_operation('create', vals)

    def action_write(self, vals={}):
        return self._execute_operation('write', vals)
