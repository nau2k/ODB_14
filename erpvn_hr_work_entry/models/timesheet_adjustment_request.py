# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class TimesheetAdjustmentRequest(models.Model):
    _name = 'timesheet.adjustment.request'
    _description = 'Timesheet Adjustment Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated'), ('cancelled', 'Cancelled')], default='draft', tracking=True)
    line_ids = fields.One2many('timesheet.adjustment.request.line', 'order_id', string='Request Line')
    note = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True, default=lambda self: self.env.company)

    def action_set_to_draft(self):
        adjustment_requests = self.filtered(lambda x: x.state == 'cancelled')
        if adjustment_requests:
            adjustment_requests.write({'state': 'draft'})
            return True
        return False

    def action_validate(self):
        adjustment_requests_to_validate = self.filtered(lambda x: x.state == 'draft')
        if adjustment_requests_to_validate:
            adjustment_requests_to_validate.line_ids.action_validate()
            adjustment_requests_to_validate.write({'state': 'validated'})
            return True
        return False

    def _cancel_request_lines(self, request_lines):
        request_lines.filtered(lambda x: x.state == 'draft').write({'state': 'validated'})

    def action_cancel(self):
        adjustment_requests_to_cancel = self.filtered(lambda x: x.state == 'draft')
        if adjustment_requests_to_cancel:
            self._validate_request(adjustment_requests_to_cancel.line_ids)
            adjustment_requests_to_cancel.write({'state': 'cancelled'})
            return True
        return False