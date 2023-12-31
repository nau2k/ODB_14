# -*- coding: utf-8 -*-
from odoo import fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    limit_date_end = fields.Integer(default=25, string='The last day for meal registration of the month.')
    receptionist_email = fields.Char(default='tien.ltn@maker64.net', string='The email address receptionist')
