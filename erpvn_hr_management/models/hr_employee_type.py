# -*- coding: utf-8 -*-
from odoo import models, fields


class HREmployeeType(models.Model):
    _name = "hr.employee.type"
    _description = "HR Employee Type"
    _inherit = ['mail.thread']

    active = fields.Boolean('Active', default=True, tracking=True)
    name = fields.Char('Name', required=True, tracking=True)
    description = fields.Text(string="description")
    member_ids = fields.One2many('hr.employee', 'employee_type_id', string='Members', readonly=True)
    is_domain = fields.Boolean(string='Can Domain', default=True)
    