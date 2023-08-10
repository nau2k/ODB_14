# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    workcenter_id = fields.Many2one('mrp.workcenter', 'WorkCenter')    
    is_progress = fields.Boolean(string=_('Is Working?'), default=False, help="For check out in scan MRP.")