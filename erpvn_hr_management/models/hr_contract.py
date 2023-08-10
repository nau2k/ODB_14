# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    def _get_default_notice_days(self):
        if self.env['ir.config_parameter'].sudo().get_param('erpvn_hr_management.notice_period'):
            return self.env['ir.config_parameter'].sudo().get_param('erpvn_hr_management.no_of_days')
        else:
            return 0

    notice_days = fields.Integer(string="Notice Period", default=_get_default_notice_days, help='Number days notice open resignation')
    
    

    # "context = no_update_resource_calendar" không thay đổi field resource_calendar_id ở employee
    def write(self, vals):
        res = super(HrEmployeeContract,  self.with_context(no_update_resource_calendar=True)).write(vals)
        return res
