# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    department_id = fields.Many2one(string='Department', comodel_name='hr.department')
    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee')
