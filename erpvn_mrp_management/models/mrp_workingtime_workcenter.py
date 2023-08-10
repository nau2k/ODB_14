# -*- coding: utf-8 -*-
from odoo import tools, models, fields, api, _


class MrpWorkingtimeWorkcenter(models.Model):
    _name = 'mrp.workingtime.workcenter'
    _order = 'bom_id, workcenter_id, id'
    _description = 'Working Time WorkCenter'
    
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10, readonly=True)
    bom_id = fields.Many2one('mrp.bom', 'BoM', index=True, ondelete='cascade')
    version = fields.Integer('BoM Version')

    workcenter_id = fields.Many2one('mrp.workcenter', "Work Center")
    working_time = fields.Float('Actual Time (hh:ss)',)
    scheduled_time = fields.Float('Scheduled Time (hh:ss)',)
    total_working_time = fields.Float('Total Actual Time (hh:ss)',)
    total_scheduled_time = fields.Float('Total Scheduled Time (hh:ss)',)