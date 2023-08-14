# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'
    
    #Citizenship
    state_id= fields.Many2one('res.country.state', 'State', domain="[('country_id', '=', country_id)]")
    district_id = fields.Many2one('res.country.district', 'District', domain="[('state_id', '=', state_id)]")
    ward_id = fields.Many2one('res.country.ward', 'Ward', domain="[('district_id', '=', district_id)]")
    street  = fields.Char('Stress')
    
    #Identification ID
    identification_country_id= fields.Many2one('res.country', 'ID Country',)
    identification_state_id= fields.Many2one('res.country.state', 'ID State', domain="[('country_id', '=', identification_country_id)]")
    identification_district_id = fields.Many2one('res.country.district', 'ID District', domain="[('state_id', '=', identification_state_id)]")
    identification_ward_id = fields.Many2one('res.country.ward', 'ID Ward', domain="[('district_id', '=', identification_district_id)]")
    identification_street  = fields.Char('ID Stress')


    @api.onchange('country_id')
    def _onchange_country_id(self):
        self.state_id = False
        self.district_id = False
        self.ward_id = False
        self.street = False

    @api.onchange('state_id')
    def _onchange_state_id(self):
        self.district_id = False
        self.ward_id = False
        self.street = False

    @api.onchange('district_id')
    def _onchange_district_id(self):
        self.ward_id = False
        self.street = False

    @api.onchange('ward_id')
    def _onchange_ward_id(self):
        self.street = False
        
    @api.onchange('identification_country_id')
    def _onchange_identification_country_id(self):
        self.identification_state_id = False
        self.identification_district_id = False
        self.identification_ward_id = False
        self.identification_street = False

    @api.onchange('identification_state_id')
    def _onchange_identification_state_id(self):
        self.identification_district_id = False
        self.identification_ward_id = False
        self.identification_street = False

    @api.onchange('identification_district_id')
    def _onchange_identification_district_id(self):
        self.identification_ward_id = False
        self.identification_street = False 

    @api.onchange('identification_ward_id')
    def _onchange_identification_ward_id(self):
        self.identification_street = False


