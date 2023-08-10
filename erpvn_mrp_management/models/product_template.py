# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductCategory(models.Model):
    _inherit = "product.category"

    categ_code = fields.Char( store=True, string="Category Code",
        help="This field related to category code, for creating customize product variant in sale order")

class ProductTemplate(models.Model):
    _inherit = "product.template"

    categ_code = fields.Char(related="categ_id.categ_code", store=True, string="Category Code",
        help="This field related to category code, for creating customize product variant in sale order")
    template_code = fields.Char(string='Template Code', store=True, compute="_get_default_template_code")

    @api.depends('categ_id')
    def _get_default_template_code(self):
        for product_tmpl in self:
            if product_tmpl.categ_id.production_location_id:
                product_tmpl.property_stock_production = product_tmpl.categ_id.production_location_id or self._get_default_production_loc()
    
    def _get_default_production_loc(self):
        return self.env['stock.location'].sudo().search([('usage', '=', 'production')], order='id', limit=1)