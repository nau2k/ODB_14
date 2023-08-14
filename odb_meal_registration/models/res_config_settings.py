# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    limit_date_end = fields.Integer(readonly=False, related='company_id.limit_date_end', string='The last day for meal registration of the month.')
    receptionist_email = fields.Char(readonly=False, default='tien.ltn@maker64.net', related='company_id.receptionist_email', string='The email address receptionist')