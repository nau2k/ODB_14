# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values, bom):
        res = super(StockRule, self)._prepare_mo_vals(product_id, product_qty, product_uom, location_id, name, origin, company_id, values, bom)
        res['bom_time_produce'] = bom.time_produce * product_qty
        res['bom_total_time'] = 0.0
        return res