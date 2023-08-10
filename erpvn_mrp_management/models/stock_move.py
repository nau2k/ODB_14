# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockMove(models.Model):
    _inherit='stock.move'

    parent_production_product_id = fields.Many2one('product.product', 'Parent MO Product Name',
        related='raw_material_production_id.product_id', store=True)
    mo_lv = fields.Integer(string='Lv', related='raw_material_production_id.mo_lv',
        store=True, default=1, readonly=True, compute='_compute_mo_bom_lv' )
    
    @api.depends('raw_material_production_id')
    def _compute_mo_bom_lv(self):
        for record in self:
            if record.raw_material_production_id:
                record.mo_lv = record.raw_material_production_id.mo_lv + 1

    def action_print_picking(self):
        for rec in self:
            if rec.picking_id:
                data = rec.picking_id.ids
                return self.env.ref("stock.action_report_picking").report_action(docids=data,config=False)
