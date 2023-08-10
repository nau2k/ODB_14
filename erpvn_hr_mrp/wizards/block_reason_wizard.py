# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import fields, models, _


class StockPickingWizard(models.TransientModel):
    _name = "block.reason.wizard"
    _description = "Block Reason Wizard"

    workorder_id = fields.Many2one('mrp.workorder', 'Work Order')
    block_reson_id = fields.Many2one('mrp.workcenter.productivity.loss', "Block Reason", required=True)
    note = fields.Text('Note')

    def button_block(self):
        timeline_obj = self.env['mrp.workcenter.productivity']
        workorder_id = self.workorder_id
        workorder_id.update({'state': 'cancel', 'block_reson_id': self.block_reson_id.id, 'note': self.note})
        for timeline in timeline_obj.search([('workorder_id', '=', workorder_id.id), ('date_end', '=', False)], limit=None):
            timeline.write({'date_end': datetime.now(), 'state': 'cancel', 'loss_id': self.block_reson_id.id, 'description': self.note})
        workorder_id.update_sequence()
        return True