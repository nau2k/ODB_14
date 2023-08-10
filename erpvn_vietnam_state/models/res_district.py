# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class ResDistrict(models.Model):  
    _name = 'res.country.district'


    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active')

    
    province_id = fields.Many2one('res.country.province', string='Province')
    state_id = fields.Many2one('res.country.state', string='State')
    ward_ids = fields.One2many('res.country.ward', 'district_id', string='Ward')