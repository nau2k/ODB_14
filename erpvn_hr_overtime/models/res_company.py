# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    limited_overtime_per_year = fields.Float(default=300.0, string='Limited Overtime Per Year')
    overtime_type = fields.Selection([('cash', 'Cash'), ('leave', 'Leave')], default='leave', string='Overtime Type')