# -*- coding: utf-8 -*-
from odoo import fields, models, _


class HROvertimeTypeRule(models.Model):
    _name = 'hr.overtime.type.rule'
    _description = "HR Overtime Type Rule"

    type_line_id = fields.Many2one('hr.overtime.type', string='Over Time Type')
    name = fields.Char('Name', required=True)
    from_hrs = fields.Float('From', required=True)
    to_hrs = fields.Float('To', required=True)
    hrs_amount = fields.Float('Rate', required=True)