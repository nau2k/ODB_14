# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockPickingWizard(models.TransientModel):
    _name = "stock.picking.wizard"
    _description = "Stock Picking Wizard"

    origin = fields.Char('Source Document', index=True, help="Reference of the document")
    mo_id = fields.Many2one('mrp.production', 'Production Order')
    note = fields.Text('Notes')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type')
    partner_id = fields.Many2one('res.partner', 'Contact')
    location_id = fields.Many2one('stock.location', 'Source Location')
    location_dest_id = fields.Many2one('stock.location', 'Destination Location')
    move_ids_without_package = fields.One2many('stock.move.wizard', 'picking_id', string='Stock Moves')


    def action_create_raw(self):
        value = [] 
        for rec in self:
            value.append({
                'plan_id': self.mo_id.plan_id.id,
                'action_type': 'add',
                'option_add_raw': 'from_mo',
                'note':self.note,
                'raw_line_ids':[ (0, 0, rec._prepare_vals()) for rec in self.move_ids_without_package]
            })
        self.env['mrp.production.add.raw'].sudo().create(value)

class StockMoveWizard(models.TransientModel):
    _name = "stock.move.wizard"
    _description = "Stock Move Wizard"
   
    picking_id = fields.Many2one('stock.picking.wizard', 'Transfer', index=True, check_company=True, required=True)
    product_id = fields.Many2one('product.product', 'Product', check_company=True, domain="[('type', 'in', ['product', 'consu'])]", index=True, required=True)
    product_uom_qty = fields.Float('Demand', digits='Product Unit of Measure', default=0.0, required=True)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    note = fields.Text('Note')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

    def _prepare_vals(self):
        return {
            'plan_id':self.picking_id.mo_id.plan_id.id,
            'plan_line_id':self.picking_id.mo_id.plan_line_id.id,
            'root_item':self.picking_id.mo_id.root_item.id,
            'parent_mo':self.picking_id.mo_id.parent_id.id,
            'mo_id':self.picking_id.mo_id.id,
            'product_id':self.product_id.id,
            'qty_add':self.product_uom_qty,
            'product_uom':self.product_uom.id,
            'note':self.note,
        }