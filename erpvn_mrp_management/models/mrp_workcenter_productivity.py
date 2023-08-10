# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MrpWorkcenterProductivity(models.Model):
    _inherit = ['mrp.workcenter.productivity']

    qty_produced = fields.Float('Produced Quantity', default=0.0, digits='Product Unit of Measure',
        copy=False, help="The number of products already handled by this worker")
    capacity = fields.Float('Capacity', default=1.0, help="Capacity of this worker.")
    state = fields.Selection([
        ('pause', 'Paused'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='Status',
        default='progress', copy=False, readonly=True)
    error = fields.Selection([('no_error', 'No Error'), ('work_center', 'Work Center')], 
        string='Error', default='no_error', copy=False, readonly=True)
    data_type = fields.Selection(related='workorder_id.data_type', string='Data Type')
    qty_product = fields.Float(related='production_id.product_qty', string='Product Quantity', store=True)