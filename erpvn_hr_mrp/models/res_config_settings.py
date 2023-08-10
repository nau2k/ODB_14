# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lock_start_wo = fields.Boolean("Lock Start WO", default=lambda self: self.env.company.po_lock == 'allow')
    limit_overtime_to_plan_workorder = fields.Float("Limit Overtime To Plan Work Order", readonly=False, related='company_id.limit_overtime_to_plan_workorder')
