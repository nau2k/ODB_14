# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MrpBomSelectionWizard(models.TransientModel):
    _name = "mrp.bom.selection.wizard"
    _description = "MRP BoM Selection Wizard"

    product_id = fields.Many2one('product.product', string='Product')
    wizard_bom_id = fields.Many2one('mrp.bom', string='Product BoM')

    def open_view_bom(self):
        self.ensure_one()
        if not self.wizard_bom_id:
            raise ValidationError(_('Select product BoM to open.'))

        bom_form_view = self.env.ref('mrp.mrp_bom_form_view')
        return {
            'name': _('BoM'),
            'res_id': self.wizard_bom_id.id,
            'res_model': 'mrp.bom',
            'type': 'ir.actions.act_window',
            'view_id': bom_form_view.id,
            'views': [(bom_form_view.id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
        }
   
