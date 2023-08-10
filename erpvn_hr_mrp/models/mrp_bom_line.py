# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    selectable_department_ids = fields.Many2many('hr.department',)
