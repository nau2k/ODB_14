# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    department_id = fields.Many2one(string='Department', comodel_name='hr.department', store=True, 
        ondelete='restrict', related='workcenter_id.department_id', readonly=True)
    number_of_workers = fields.Integer(string='Number of Workers', default=1)