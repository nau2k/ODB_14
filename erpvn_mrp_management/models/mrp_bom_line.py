# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import math


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.depends('product_qty', 'product_loss', 'multiple_qty')
    def _sum_product_loss(self):
        for obj in self:
            technical_qty = obj.product_qty * (100 / float(obj.product_loss))
            if obj.multiple_qty > 0.0:
                num_qty = int(math.ceil(obj.product_qty / obj.multiple_qty)) * obj.multiple_qty
                technical_qty = num_qty * (100 / float(obj.product_loss))
            obj.sudo().write({'technical_qty': technical_qty})

    @api.onchange('product_qty', 'product_loss', 'multiple_qty')
    def onchange_compute_product_loss(self):
        self = self.sudo()
        for obj in self:
            if obj.product_loss < 1:
                obj.product_loss = 1
            if obj.product_loss > 100:
                obj.product_loss = 100
            if obj.multiple_qty < 0.0:
                obj.multiple_qty = 0.0
        self._sum_product_loss()

    barcode = fields.Char(string='Barcode', related='product_id.barcode', readonly=True, store=True)
    time_produce = fields.Float('Time Produce (mins)', default=0.0)
    seq = fields.Integer(string="Seq", related='sequence', store=True)
    boms_count = fields.Integer('BoMs Count', compute='_compute_boms_count')

    # Technical_qty dùng để tính số lượng hao hụt dự kiến của BoM
    # Multi_qty Số lượng thực tế của các sản phẩm do lương theo mét tới, như cuộn vải, cuộn thép
    # Product_loss Là ổng của số lượng trong line + với số lượng hao hụt
    technical_qty = fields.Float('Technical Qty', default=1.0, 
        compute=_sum_product_loss, digits='Product Unit of Measure')
    multiple_qty = fields.Float('Multi Qty', default=0.0, digits='Product Unit of Measure')
    product_loss = fields.Integer("Recovery (%)", required=True, default=100,
        help="A factor of 0.9 means a loss of 10% within the production process.",)
    product_qty = fields.Float('Quantity', digits='Product Unit of Measure', store=True)

    @api.constrains('product_loss')
    def _validate_product_loss(self):
        for record in self:
            if record.product_loss < 1 or record.product_loss > 100:
                raise ValidationError(_("Recovery must be a integer and have value between 1 - 100."))

    @api.constrains('multiple_qty')
    def _validate_multiple_qty(self):
        for record in self:
            if record.multiple_qty < 0.0:
                raise ValidationError(_("Multiple Quantity must be a positive float."))

    @api.depends('product_id')
    def _compute_boms_count(self):
        for line in self:
            line.boms_count = self.env['mrp.bom'].sudo().search_count([('product_id', '=', line.product_id.id)])

    @api.constrains('product_uom_id')
    def _check_uom_category(self):
        tmpl_uom_categ_id = self.product_tmpl_id.uom_id.category_id
        if self.product_uom_id.category_id != tmpl_uom_categ_id:
            raise UserError(_("Uom category does not macth with template"))

    @api.model
    def create(self, vals):
        if not vals.get('sequence', False) and vals.get('bom_id', False):
            seq = 10
            bom_id = self.env['mrp.bom'].browse(vals.get('bom_id'))
            if bom_id and bom_id.bom_line_ids:
                seq_list = list(set(bom_id.bom_line_ids.mapped('sequence')))
                if vals.get('sequence') in seq_list:
                    seq = max(seq_list) + 10
            vals.update({'sequence': seq})
        return super(MrpBomLine, self).create(vals)

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


    def _prepare_extra_plan_vals(self):
        self.ensure_one()
        return {
            'sequence': self.sequence,
            'seq': self.seq,
            'product_id': self.product_id.id,
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'product_uom_category_id': self.product_uom_category_id.id,
            'parent_bom_id': self.bom_id.id,
            'operation_id': self.operation_id.id,
            'time_produce': self.time_produce,
            'company_id': self.company_id.id,
            'technical_qty': self.technical_qty,
            'product_loss': self.product_loss,
            'multiple_qty': self.multiple_qty,
        }

    def move_line_to_extra_plan(self):
        vals = self._prepare_extra_plan_vals()
        extra_plan_id = self.env['bom.extra.plan'].create(vals)
        
        if extra_plan_id:
            vals['action'] = 'create'
            vals['model'] = 'extra'
            self.env['mrp.bom.line']._log_message(self.bom_id, False, vals)
            self._log_message(self.bom_id, self, {'action': 'unlink'})
            self.unlink()

    def _log_message(self, record, bom_line, vals):
        data = vals.copy()

        if vals['action'] == 'write':
            if 'product_uom_id' in vals:
                data['product_uom_id'] = self.env['uom.uom'].browse(vals.get('product_uom_id')).name
            if 'product_id' in vals:
                data['product_id'] = self.env['product.product'].browse(vals.get('product_id')).display_name
        elif vals['action'] == 'unlink':
            data['product_id'] = bom_line.product_id.display_name
            data['product_uom_id'] = bom_line.product_uom_id.name
            data['technical_qty'] = bom_line.technical_qty
        elif vals['action'] == 'create':
            data['product_id'] = self.env['product.product'].browse(vals.get('product_id')).display_name
            data['product_uom_id'] = self.env['uom.uom'].browse(vals.get('product_uom_id')).name

            technical_qty = vals.get('product_qty') * (100 / float(vals.get('product_loss')))
            if vals.get('multiple_qty', 0) > 0.0:
                num_qty = int(math.ceil(vals.get('product_qty') / vals.get('multiple_qty'))) * vals.get('multiple_qty')
                technical_qty = num_qty * (100 / float(vals.get('product_loss')))
            data['technical_qty'] = technical_qty

        record.message_post_with_view(
            'erpvn_mrp_management.mail_message_update_bom_value', 
            values={'bom_line': bom_line, 'vals': dict(vals, **data)}, 
            subtype_id=self.env.ref('mail.mt_note').id
        )

    def write(self, vals):
        for bom_line in self:
            if any(field in vals for field in ('product_id', 'product_qty', 'multiple_qty', 'product_uom_id')):
                msg_vals = vals.copy()
                msg_vals['action'] = 'write'
                bom_line._log_message(bom_line.bom_id, bom_line, msg_vals)
        return super(MrpBomLine, self).write(vals)