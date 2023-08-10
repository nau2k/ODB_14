# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResourceCalendarLeaves(models.Model):
    _inherit = 'resource.calendar.leaves'

    department_id = fields.Many2one(string='Department', comodel_name='hr.department', 
        related='resource_id.department_id', store=True, readonly=True)
    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee',
        related='resource_id.employee_id', store=True, readonly=True)
    duration = fields.Float('Time Need', compute='_compute_duration', store=True, digits=(5,1))
    time_processed = fields.Float('Time Processed', readonly=True)
    hours_per_day = fields.Float(string='Average Hour per Day', related='calendar_id.hours_per_day', readonly=True)
    state = fields.Selection(string='Status', selection=[('waiting', 'Todo'), ('done', 'Done')],default='waiting')
    date_from = fields.Datetime(store=True)
    date_to = fields.Datetime(store=True)
    
    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for leave in self:
            res = 0.0
            if leave.date_from and leave.date_to:
                res = (leave.date_to - leave.date_from).total_seconds() / 3600

            leave.duration = res

    def recompute_duration(self):
        self._compute_duration()