# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class ResCountryState(models.Model):  
    _inherit = 'res.country.state'

    
    district_ids = fields.One2many('res.country.district', 'state_id', string='District')
