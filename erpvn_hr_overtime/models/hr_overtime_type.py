# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HROvertimeType(models.Model):
    _name = 'hr.overtime.type'
    _description = "HR Overtime Type"

    name = fields.Char('Name')
    type = fields.Selection([('cash', 'Cash'), ('leave', 'Leave ')])
    duration_type = fields.Selection([('hours', 'Hour'), ('days', 'Days')], string="Duration Type", default="hours", required=True)
    leave_type = fields.Many2one('hr.leave.type', string='Leave Type', domain="[('id', 'in', leave_compute)]")
    leave_compute = fields.Many2many('hr.leave.type', compute="_get_leave_type")
    rule_line_ids = fields.One2many('hr.overtime.type.rule', 'type_line_id')

    @api.onchange('duration_type')
    def _get_leave_type(self):
        leave_type_ids = self.env['hr.leave.type'].search([('request_unit', '=', self.duration_type)])
        self.write({'leave_compute': [(6, 0, leave_type_ids.ids)]})