# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class EmployeeRelationInfo(models.Model):
    """Table for keep employee family information"""
    _name = 'hr.employee.relation'
    _description = 'HR Employee Relation'

    
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of follow-up lines.")
    name = fields.Char(string="Relationship", help="Relationship with thw employee", translate=True)
    is_children = fields.Boolean(string='Is Children?', default=False)