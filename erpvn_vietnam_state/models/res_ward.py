# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class ResWard(models.Model):  
    _name = 'res.country.ward'


    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active')
    district_id = fields.Many2one('res.country.district', string='District')

