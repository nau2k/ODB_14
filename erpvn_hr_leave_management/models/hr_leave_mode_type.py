# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrLeaveTypeGroup(models.Model):
    _name = 'hr.leave.mode.type'
    _description = 'HR Leave Mode Type'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', size=8)
    description = fields.Text(string='Description',)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    type_ids = fields.One2many(string='Leaves Type', comodel_name='hr.leave.type', inverse_name='mode_id',)