# -*- coding: utf-8 -*-
from odoo import models, fields, _


class HrEmployees(models.Model):
    _inherit = 'hr.employee.public'

    attendance_late_count = fields.Integer(string="Attendance Late", compute="_get_attendance_late_count")

    def action_view_attendance_late_count(self):
        domain = [
            ('employee_id', '=', self.id),
        ]
        return {
            'name': _('Employee Attendance Late'),
            'domain': domain,
            'res_model': 'hr.attendance.late',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'limit': 80,
        }

    def _get_attendance_late_count(self):
        for employee in self:
            employee.attendance_late_count = self.env['hr.attendance.late'].search_count([('employee_id', '=', employee.id)])
