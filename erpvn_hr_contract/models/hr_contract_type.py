# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HRContractType(models.Model):
    _name = "hr.contract.type"
    _description = "HR Contract Type"
    _inherit = ['mail.thread']

    active = fields.Boolean('Active', default=True, tracking=True)
    name = fields.Char('Contract Type', required=True, tracking=True)
    is_trial = fields.Boolean('Is Trial?', default=False, copy=False, tracking=True)
    range_days = fields.Float('Number of months/days', default=0.0, tracking=True)
    num_of_range = fields.Integer('Number of range', compute='_compute_num_of_range', store=True)
    range_type = fields.Selection([('days', 'Days'), ('months', 'Months')], required=True, default='days', tracking=True)
    date_start = fields.Datetime(string='From', tracking=True)
    date_stop = fields.Datetime(string='To', tracking=True)

    @api.depends('range_days')
    def _compute_num_of_range(self):
        for record in self:
            record.num_of_range = int(record.range_days)