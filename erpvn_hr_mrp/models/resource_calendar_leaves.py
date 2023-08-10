# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResourceCalendarLeaves(models.Model):
    _inherit = 'resource.calendar.leaves'

    production_id = fields.Many2one('mrp.production', 'Manufacturing Order', check_company=True, readonly=True)
    workorder_id = fields.Many2one('mrp.workorder', 'Work Order', check_company=True, readonly=True)
    workcenter_id = fields.Many2one(string='WorkCenter', comodel_name='mrp.workcenter',
        related='resource_id.workcenter_id', store=True, readonly=True)