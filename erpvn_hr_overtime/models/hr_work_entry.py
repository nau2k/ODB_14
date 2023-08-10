# -*- coding: utf-8 -*-
from odoo import fields, models


class HRWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    is_overtime = fields.Boolean(string='Is Overtime?', tracking=True)
    overtime_id = fields.Many2one('hr.overtime', string='Overtime')
    overtime_line_id = fields.Many2one('hr.overtime.line', string='Overtime Line')
