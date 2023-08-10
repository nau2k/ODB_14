# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class Company(models.Model):
    _inherit = 'res.company'

    mo_check_raw = fields.Selection([
        ('check', 'Check available raws before start WO in MO'),
        ('allow', 'Allow start WO without check available raws in MO')
        ], string="Check Available Raw", default="allow")
    limit_overtime_to_plan_workorder = fields.Float(default=120)
