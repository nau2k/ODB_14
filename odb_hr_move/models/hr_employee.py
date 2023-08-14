# -*- coding: utf-8 -*-
from odoo import models, fields, api, _



class HrEmployeeMove(models.Model):  
    _inherit = 'hr.employee'

    
    move_ids = fields.One2many('hr.move', 'employee_id', string='Move')
