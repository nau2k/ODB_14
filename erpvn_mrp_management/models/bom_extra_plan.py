# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import math

class BomExtraPlan(models.Model):
    _name = 'bom.extra.plan'
    _order = "parent_bom_id, sequence, id"
    _rec_name = "product_id"
    _description = 'BOM Extra Plan'
    _check_company_auto = True

    def _get_default_product_uom(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    @api.depends('product_qty', 'product_loss', 'multiple_qty')
    def _sum_product_loss(self):
        for obj in self:
            technical_qty = obj.product_qty * (100 / float(obj.product_loss))
            if obj.multiple_qty > 0.0:
                num_qty = int(math.ceil(obj.product_qty / obj.multiple_qty)) * obj.multiple_qty
                technical_qty = num_qty * (100 / float(obj.product_loss))
            obj.write({'technical_qty': technical_qty})

    sequence = fields.Integer('Sequence', default=1, help="Gives the sequence order when displaying.")
    seq = fields.Integer(string="Seq", related='sequence', store=True)
    product_id = fields.Many2one('product.product', 'Product', required=True, check_company=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    product_qty = fields.Float('Quantity', default=1.0, digits='Product Unit of Measure', required=True)
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', default=_get_default_product_uom,
        required=True, domain="[('category_id', '=', product_uom_category_id)]",
        help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    operation_id = fields.Many2one(
        'mrp.routing.workcenter', 'Consumed in Operation', check_company=True,
        domain="[('id', 'in', allowed_operation_ids)]",
        help="The operation where the components are consumed, or the finished products created.")
    parent_bom_id = fields.Many2one('mrp.bom', 'Parent BoM', ondelete='cascade', required=True)
    parent_product_tmpl_id = fields.Many2one('product.template', 'Parent Product Template', related='parent_bom_id.product_tmpl_id')
    product_bom_id = fields.Many2one('mrp.bom', 'Product BoM', compute='_compute_product_bom', readonly=False, store=True)
    time_produce = fields.Float('Time Produce (mins)', default=0.0)

    company_id = fields.Many2one(related='parent_bom_id.company_id', store=True, index=True, readonly=True)
    boms_count = fields.Integer('BoMs Count', compute='_compute_boms_count')

    technical_qty = fields.Float('Technical Qty', default=1.0, 
        compute=_sum_product_loss, digits='Product Unit of Measure')
    multiple_qty = fields.Float('Multi Qty', default=0.0, digits='Product Unit of Measure')
    product_loss = fields.Integer("Recovery (%)", required=True, default=100,
        help="A factor of 0.9 means a loss of 10% within the production process.",)

    @api.depends('product_id')
    def _compute_boms_count(self):
        for record in self:
            record.boms_count = self.env['mrp.bom'].search_count([('product_id', '=', record.product_id.id)])

    _sql_constraints = [
        ('extra_plan_qty_zero', 'CHECK (product_qty>=0)', 'All product quantities must be greater or equal to 0.'),
    ]

    @api.depends('product_id')
    def _compute_product_bom(self):
        for record in self:
            product_bom_id = False
            if record.product_id:
                product_bom_id = self.env['mrp.bom']._bom_find(product_tmpl=record.product_id.product_tmpl_id, product=record.product_id)
            record.write({'product_bom_id': product_bom_id})

    def _prepare_bom_line_vals(self):
        self.ensure_one()
        return {
            'sequence': self.sequence,
            'seq': self.seq,
            'product_id': self.product_id.id,
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'product_uom_category_id': self.product_uom_category_id.id,
            'bom_id': self.parent_bom_id.id,
            'time_produce': self.time_produce,
            'operation_id': self.operation_id.id,
            'company_id': self.company_id.id,
            'technical_qty': self.technical_qty,
            'product_loss': self.product_loss,
            'multiple_qty': self.multiple_qty,
        }

    def move_line_to_bom_line(self):
        vals = self._prepare_bom_line_vals()
        bom_line_id = self.env['mrp.bom.line'].create(vals)
        if bom_line_id:
            vals['action'] = 'create'
            self.env['mrp.bom.line']._log_message(bom_line_id.bom_id, False, vals)
            bom_line_id._log_message(bom_line_id.bom_id, bom_line_id, {'action': 'unlink', 'model': 'extra'})
            self.unlink()

    def action_see_bom_childs(self):
        bom_ids = self.env['mrp.bom'].search([('product_id', '=', self.product_id.id)])
        if len(bom_ids) > 1:
            wizard_view = self.env.ref('erpvn_mrp_management.mrp_bom_selection_wizard_form_view')
            return {
                'name': _('Select BoM To Open'),
                'domain': [('id', 'in', bom_ids.ids)],
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mrp.bom.selection.wizard',
                'views': [(wizard_view.id, 'form')],
                'view_id': wizard_view.id,
                'target': 'new',
                'context': {'default_product_id': self.product_id.id},
            }
        elif len(bom_ids) == 1:
            bom_form_view = self.env.ref('mrp.mrp_bom_form_view')
            return {
                'res_id': bom_ids.id,
                'res_model': 'mrp.bom',
                'type': 'ir.actions.act_window',
                'view_id': bom_form_view.id,
                'views': [(bom_form_view.id, 'form')],
                'view_type': 'form',
                'view_mode': 'form',
            }
        else:
            msg = _("Product %s does not has BoM yet!" % self.product_id.display_name)
            message_id = self.env['message.wizard'].create({'message': msg})
            return {
                'name': _('Notification'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                'res_id': message_id.id,
                'target': 'new',
            }
        
    def write(self, vals):
        for extra_line in self:
            if any(field in vals for field in ('product_id', 'product_qty', 'multiple_qty', 'product_uom_id')):
                msg_vals = vals.copy()
                msg_vals['action'] = 'write'
                msg_vals['model'] = 'extra'
                self.env['mrp.bom.line']._log_message(extra_line.parent_bom_id, extra_line, msg_vals)
        return super(BomExtraPlan, self).write(vals)