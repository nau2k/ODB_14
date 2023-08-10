# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ProductCategory(models.Model):
    _inherit = "product.category"

    @api.model
    def _get_default_production_location(self):
        # for rec in self:
        #     if rec.parent_id:
        #         return rec.parent_id.production_location_id
        # return self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
        if self.parent_id:
            return self.parent_id.production_location_id
        return self.env['stock.location'].search([('usage', '=', 'production')], limit=1)
    
    production_location_id = fields.Many2one('stock.location', "Production Location",
        default=_get_default_production_location, domain="[('usage', '=', 'production')]",
        help="This stock location will be used, instead of the default one, as the source location for stock moves generated by manufacturing orders.")
    
    def action_update_location_production(self):
        for categ_id in self:
            product_tmpl_ids = self.env['product.template'].search([('categ_id', '=', categ_id.id)])
            product_tmpl_ids._get_default_template_code()