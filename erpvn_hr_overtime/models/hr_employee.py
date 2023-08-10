# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    overtime_line_ids = fields.One2many('hr.overtime.line', 'employee_id', string='Overtime Shifts')
    allowed_overtime_hours = fields.Float(related='company_id.limited_overtime_per_year', string='Allowed Overtime Hours', store=True)
    remain_overtime_hours = fields.Float(compute='_compute_remain_overtime_hours', string='Remain Overtime Hours', store=True)

    @api.depends('overtime_line_ids')
    def _compute_remain_overtime_hours(self):
        for employee in self:
            valid_ot_shift_ids = employee.overtime_line_ids.filtered(lambda x: x.overtime_id and x.hour_from and x.hour_to and x.status == 'valid')
            overtime_hours = sum(valid_ot_shift_ids.filtered(lambda x: x.overtime_id.overtime_day.year == fields.Date.today().year).mapped('duration'))
            employee.write({'remain_overtime_hours': employee.allowed_overtime_hours - overtime_hours})
    