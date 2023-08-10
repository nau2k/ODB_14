# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    sequence = fields.Integer(default=10000)
    seq = fields.Integer(related='sequence', string='Seq', store=True)
    product_id = fields.Many2one(string='Product', comodel_name='product.product', 
        ondelete='restrict', related='bom_id.product_id', readonly=True)
    time_cycle_manual = fields.Float(
        'Manual Duration', default=1,
        help="Time in minutes:"
        "- In manual mode, time used"
        "- In automatic mode, supposed first time when there aren't any work orders yet")

    @api.constrains('sequence')
    def _check_sequence(self):
        for routing_id in self:
            if routing_id.sequence < 9999:
                raise ValidationError(_('The sequence of a Routing should contain more than 4 numbers'))