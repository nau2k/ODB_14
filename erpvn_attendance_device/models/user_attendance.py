# -*- coding: utf-8 -*-
from odoo import  models, fields, api, _


class UserAttendance(models.Model):
    _name = 'user.attendance'
    _description = 'User Attendance'
    _order = 'timestamp DESC, user_id, status, attendance_state_id, device_id'

    device_id = fields.Many2one('attendance.device', string='Attendance Device',
        required=True, ondelete='restrict', index=True)
    user_id = fields.Many2one('attendance.device.user', string='Device User',
        required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', related='user_id.employee_id', store=True, index=True)
    timestamp = fields.Datetime(string='Timestamp', required=True, index=True)
    attendance_state_id = fields.Many2one('attendance.state', string='Odoo Attendance State', index=True,
        help='This technical field is to map the attendance status stored in the device and the attendance status in Odoo')
    work_entry_type_id = fields.Many2one('hr.work.entry.type', related='attendance_state_id.work_entry_type_id', index=True)
    hr_attendance_id = fields.Many2one('hr.attendance', string='HR Attendance', ondelete='set null',
        help='The technical field to link Device Attendance Data with Odoo\' Attendance Data', index=True)
    type = fields.Selection(string='Activity Type', related='attendance_state_id.type', store=True)
    valid = fields.Boolean(string='validated', index=True, readonly=True, default=False,
        help="This field is to indicate if this attendance record is valid for HR Attendance Synchronization."
        " E.g. The Attendances with Check out prior to Check in or the Attendances for users without employee  mapped will not be valid.")
    inconsistent_state = fields.Selection([('valid', 'Validated'),
        ('inconsistent', 'Inconsistent'),
        ('duplicate', 'Duplicate')], 'Status', required=True, readonly=True, default='valid')
    reason = fields.Text('Reason', readonly=True)
    is_attedance_created = fields.Boolean(string="Is Attendance")
    status = fields.Integer(string='Device Attendance State', help='The state which is the unique number stored in the device to indicate type of attendance (e.g. 0: check_in, 1: check_out, etc)')
    
    _sql_constraints = [
        ('unique_user_id_device_id_timestamp',
         'UNIQUE(user_id, device_id, timestamp)',
         "The Timestamp and User must be unique per Device"),
    ]

    @api.constrains('status', 'attendance_state_id')
    def constrains_status_attendance_state_id(self):
        for r in self:
            if r.status != r.attendance_state_id.code:
                raise(_('Attendance Status conflict! The status number from device must match the attendance status defined in Odoo.'))

    def valid_att(self):
        for attendance in self:
            attendance.update({'valid': attendance.is_valid()})

    def is_valid(self):
        self.ensure_one()
        if not self.employee_id:
            return False
        prev_att = self.search([('employee_id', '=', self.employee_id.id),
                                ('timestamp', '<', self.timestamp),
                                ('work_entry_type_id', '=', self.work_entry_type_id.id),
                                ('is_attedance_created', '=', False),], limit=1, order='timestamp DESC')
        if not prev_att:
            valid = self.type == 'check_in' and True or False
        else:
            valid = prev_att.type != self.attendance_state_id.type and True or False
            if not valid:
                self.update({'inconsistent_state': 'inconsistent'})
        return valid

    @api.model_create_multi
    def create(self, val_list):
        attendances = super(UserAttendance, self).create(val_list)
        valid_attendances = attendances.filtered(lambda att: att.is_valid())
        if valid_attendances:
            valid_attendances.write({'valid': True})
        return attendances

    def action_attendace_validated(self):
        # total_employee = self.env['hr.employee'].search([])
        att_pool = self.env['user.attendance']
        # Cầu 1 filter ở đây để lọc các giá trị employee_id và valid
        for val in self:
            if not val.employee_id or not val.valid:
                continue
            user_att = att_pool.search([
                    ('employee_id', '=', val.employee_id.id),
                    ('timestamp', '<=', val.timestamp),
                    ('type', '!=', val.type),
                    ('is_attedance_created', '=', False)
                ], order="timestamp asc",limit=1)
            if user_att:
                existing_attendance = self.env['hr.attendance'].search(
                    [('employee_id', '=', user_att.employee_id.id), ('check_in', '<=', user_att.timestamp), ('check_out', '=', False)])
                if existing_attendance:
                    existing_attendance.update({
                        'check_out': user_att.timestamp,
                        'device_out_id': user_att.device_id.id,
                    })
                    val.update({
                        'is_attedance_created': True
                    })

                elif not existing_attendance:
                    vals = {
                        'employee_id': user_att.employee_id.id,
                        'check_in': user_att.timestamp,
                        'device_in_id': user_att.device_id.id,
                    }
                    hr_attendance = self.env['hr.attendance'].create(vals)
                    val.update({
                        'is_attedance_created': True,
                        'hr_attendance_id': hr_attendance.id,
                    })
