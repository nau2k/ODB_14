# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Department(models.Model):
    _inherit = ['hr.department']

    is_production = fields.Boolean(string='Is Production',)
    
    