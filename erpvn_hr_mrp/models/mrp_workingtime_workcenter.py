# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MrpWorkingtimeWorkcenter(models.Model):
    _inherit = 'mrp.workingtime.workcenter'
    
    department_id = fields.Many2one(string='Department', comodel_name='hr.department',
        ondelete='restrict', related='workcenter_id.department_id', readonly=True)