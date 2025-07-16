
from odoo import fields, models

ATTENDANCE_STATUS = [
    ('new', 'New'),
    ('success', 'Success'),
    ('fail', 'Fail'),
]

class AttendanceSyncLog(models.Model):
    _name = "attendance.sync.log"
    _rec_name = 'employee_id'

    employee_id=fields.Many2one(comodel_name='hr.employee',string="Employee ID")
    attendance_id = fields.Many2one(comodel_name='hr.attendance',string="Attendance ID")
    queue_name = fields.Char(string="Queue Name")
    data = fields.Json(
        string="Data",
        help="JSON data received from RabbitMQ")
    state=fields.Selection(ATTENDANCE_STATUS,string="Attendance status",default='new',)

    def action_retry_sync(self):
        """Retry the sync operation for this log entry."""
        self.state = 'success'

    def action_check_in(self):
        try:
            attendance = self.env['hr.attendance'].create({
                'employee_id': self.employee_id.id,
                'check_in': fields.Datetime.now()
            })
            self.state = "success"
        except Exception as e:
            print("Error at check in :",e)

    def action_check_out(self):
        attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee_id.id),
            ('check_out', '=', False)
        ], limit=1)
        if attendance:
            attendance.write({'check_out': fields.Datetime.now()})
        print("Checkout success")
        self.state="fail"
        return True