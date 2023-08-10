# -*- coding: utf-8 -*-
from odoo import fields, models, api

class ResConfigSetting(models.TransientModel):
    _inherit = ['res.config.settings']

    notice_period = fields.Boolean(string='Notice Period')
    no_of_days = fields.Integer()

    def set_values(self):
        super(ResConfigSetting, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("erpvn_hr_management.notice_period",
                                                         self.notice_period)
        self.env['ir.config_parameter'].sudo().set_param("erpvn_hr_management.no_of_days",
                                                         self.no_of_days)

    @api.model
    def get_values(self):
        res = super(ResConfigSetting, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['notice_period'] = get_param('erpvn_hr_management.notice_period')
        res['no_of_days'] = int(get_param('erpvn_hr_management.no_of_days'))
        return res

    # @api.onchange('service_expense_journal')
    # def onchange_accounts(self):
    #     self.service_credit_account = self.service_expense_journal.default_credit_account_id.id
    #     self.service_debit_account = self.service_expense_journal.default_debit_account_id.id
