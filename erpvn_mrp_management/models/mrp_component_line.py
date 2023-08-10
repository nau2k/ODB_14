# -*- coding: utf-8 -*-
from odoo import models, fields

class MrpComponentLine(models.Model):
    _name = 'mrp.component.line'
    _description = 'MRP Component Line'
    
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10, readonly=True)
    bom_id = fields.Many2one('mrp.bom', 'BoM', index=True, ondelete='cascade')
    product_id = fields.Many2one(comodel_name='product.product', string='Product', ondelete='cascade')
    unit_product_price = fields.Float(string='Unit Price')
    type = fields.Selection([('com', 'Component'), ('raw', 'Raw'),('sub','Subcontract')], string='Type', default='raw')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure',)
    version = fields.Integer('BoM Version')
    
    line_qty = fields.Float(string='Line Qty', digits='Product Unit of Measure')
    bom_qty = fields.Float(string='BoM Qty', digits='Product Unit of Measure')
    bom_product_price = fields.Float(string='BoM Price')
    need_product_price = fields.Float(string='Need Qty Price')
    total_bom_price = fields.Float(string='Total Price')

    qty_available = fields.Float('Qty On Hand', digits='Product Unit of Measure')
    virtual_available = fields.Float('Forecast Qty', digits='Product Unit of Measure')
    free_qty = fields.Float('Free Qty ', digits='Product Unit of Measure')
    incoming_qty = fields.Float('Incoming', digits='Product Unit of Measure')
    outgoing_qty = fields.Float('Outgoing', digits='Product Unit of Measure')
    qty_reserved = fields.Float(string='Qty Reversed', digits='Product Unit of Measure')
    qty_needed = fields.Float(string='Qty Needed', digits='Product Unit of Measure')