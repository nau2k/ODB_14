# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HRBreakTimeLine(models.Model):
    _name = 'hr.break.time.line'
    _description = 'Breaking Hours Line'

    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(default=10, help="Gives the sequence of this line when displaying the resource calendar.")
    name = fields.Char(string='Name', required=True)
    break_id = fields.Many2one('hr.break.time', 'Breaktime', required=True)
    department_id = fields.Many2one('hr.department', 'Department', required=True)
    description = fields.Text(string='Description',)

    @api.constrains('name', 'break_id')
    def _check_unique_name(self):
        for record in self.filtered(lambda x: x.name):
            if record.search_count([('name', '=', record.name), ('break_id', '=', record.break_id.id), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('Breaking line must be unique per breaking hours.'))