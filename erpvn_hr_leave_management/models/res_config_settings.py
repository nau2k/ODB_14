# -*- coding: utf-8 -*-
from odoo import fields, models, api


class RestConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def _get_domain_unpaid_holiday_status(self):
        return [('valid', '=', True), ('mode_id', '!=', False), ('mode_id.code', 'in', ['UnPaid', 'Sick'])]

    unpaid_holiday_status_id = fields.Many2one(related='company_id.unpaid_holiday_status_id', domain=_get_domain_unpaid_holiday_status, readonly=False)