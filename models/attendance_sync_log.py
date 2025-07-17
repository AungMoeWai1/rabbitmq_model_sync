from email.policy import default

from odoo import fields, models

ATTENDANCE_STATUS = [
    ('new', 'New'),
    ('success', 'Success'),
    ('fail', 'Fail'),
]

ATTENDANCE_TYPE=[
    ('check_in','Check In'),
    ('check_out','Check Out'),
]

class AttendanceSyncLog(models.Model):
    _name = "attendance.sync.log"
    _rec_name = 'employee_id'

    employee_id=fields.Many2one(comodel_name='hr.employee',string="Employee ID")
    attendance_id = fields.Many2one(comodel_name='hr.attendance',string="Attendance ID")
    type=fields.Selection(ATTENDANCE_TYPE, string="Attendance Type", default='check_in', help="Type of attendance action")
    queue_name = fields.Char(string="Queue Name")
    data = fields.Json(
        string="Data",
        help="JSON data received from RabbitMQ")
    date=fields.Datetime(string="Date",default=fields.Datetime.now())
    state=fields.Selection(ATTENDANCE_STATUS,string="Attendance status",default='new',)


    def action_retry_sync(self):
        """Retry the sync operation for this log entry."""
        if self.type=='check_in':
            self._action_check_in()
        else:
            self._action_check_out()

    def _action_check_in(self):
        try:
            self.env['hr.attendance'].create({
                'employee_id': self.employee_id.id,
                'check_in': self.date
            })
            self.state = "success"
        except Exception as e:
            self.state = "fail"
            print("Error at check in :",e)

    def _action_check_out(self):
        try:
            attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', self.employee_id.id),
            ('check_out', '=', False)
            ], limit=1)
            if attendance:
                attendance.write({'check_out': self.date})
                self.state = "success"
        except Exception as e:
            self.state = "fail"
            print("Error at check out :",e)
            