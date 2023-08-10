# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PrintPickingWizard(models.TransientModel):
    _name = "print.picking.wizard"
    _description = "Print Picking Wizard"

    picking_ids = fields.Many2many('stock.picking',string="Pickings")
    picking_type = fields.Selection([
        ('out', 'Picking Component'),
        ('int', 'Post Finish Good'),
    ], string='Type',default='int')
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('done', 'Done'),
    ], string='state',default='waiting')

    def print_report(self,picking):
        return self.env.ref("stock.action_report_picking").report_action(docids=picking.ids,config=False)


    def action_print(self):
        picking_int = self.picking_ids.filtered(lambda x: x.location_dest_id != x.group_id.mrp_production_ids.location_src_id)
        picking_out = self.picking_ids.filtered(lambda x: x.location_dest_id == x.group_id.mrp_production_ids.location_src_id)
        error_mess = 'Could not find picking with the above information'
        if self.picking_type == 'int':
            if picking_int:
                if self.state =='waiting':
                    pick_int_wait = picking_int.filtered(lambda x: x.state not in  ['done','cancel'])
                    if pick_int_wait:
                        return self.print_report(pick_int_wait)
                    else:
                        raise ValidationError(_(error_mess))
                else:
                    pick_int_done = picking_int.filtered(lambda x: x.state =='done')
                    if pick_int_done :
                        return self.print_report(pick_int_done)
                    else:
                        raise ValidationError(_(error_mess))
            else:
                raise ValidationError(_(error_mess))
                
        elif self.picking_type == 'out':
            if picking_out:
                if self.state =='waiting':
                    pick_out_wait = picking_out.filtered(lambda x: x.state not in  ['done','cancel'])
                    if pick_out_wait:
                        return self.print_report(pick_out_wait)
                    else:
                        raise ValidationError(_(error_mess))
                else:
                    pick_out_done = picking_out.filtered(lambda x: x.state =='done')
                    if pick_out_done :
                        return self.print_report(pick_out_done)
                    else:
                        raise ValidationError(_(error_mess))
            else:
                raise ValidationError(_(error_mess))

