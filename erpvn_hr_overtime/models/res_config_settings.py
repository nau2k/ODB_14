# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    limited_overtime_per_year = fields.Float(related='company_id.limited_overtime_per_year',
        readonly=False, string='Limited Overtime Per Year')
    overtime_type = fields.Selection(related='company_id.overtime_type', readonly=False, string='Overtime Type')