# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResourceDepartment(models.Model):
    _name = 'resource.department'
    _description = 'Resouce Department'

    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(default=10, help="Gives the sequence of this line when displaying the resource calendar.")
    name = fields.Char(string='Name')
    calendar_id = fields.Many2one('resource.calendar', 'Calendar')   
    department_id = fields.Many2one('hr.department', 'Department', required=True)    
    description = fields.Text(string='Description',)