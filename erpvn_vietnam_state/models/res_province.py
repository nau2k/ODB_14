# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class ResDistrict(models.Model):  
    _name = 'res.country.province'


    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active')

    
    country_id = fields.Many2one('res.country', string='Country')
    district_ids = fields.One2many('res.country.district', 'province_id', string='District')