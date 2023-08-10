# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def _get_default_unpaid_holiday_status(self):
        return self.env['hr.leave.type'].search([('code', '=', 'UPUL')], limit=1)
        
    unpaid_holiday_status_id = fields.Many2one("hr.leave.type", string="Time Off Type", default=_get_default_unpaid_holiday_status, domain=[('valid', '=', True)])