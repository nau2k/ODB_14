# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    delivery_instructions = fields.Text("Delivery Instructions")
    is_customer = fields.Boolean(string='Is Customer')
    is_vendor = fields.Boolean(string='Is Vendor')