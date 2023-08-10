# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Partner(models.Model):
    _inherit = 'res.partner'

    is_internal = fields.Boolean(string='Is Internal')
    employee_id = fields.Many2one('hr.employee', string='Employee')