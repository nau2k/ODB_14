# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrContractAllowance(models.Model):
    _name = 'hr.contract.allowance'
    _description = 'HR Contract Allowance'
    _inherit = ['mail.thread']

    code = fields.Char('Code', required=True, copy=False, default='New', tracking=True)
    description = fields.Text('Description')
    amount = fields.Float('Amount', tracking=True)
    apply_on = fields.Selection([('monthly', 'Monthly'), ('daily', 'Daily'), ('hourly', 'Hourly')], string='Apply on', default='monthly', tracking=True)
    contract_id = fields.Many2one('hr.contract', 'Contract', ondelete='cascade', tracking=True)
    subcontract_id = fields.Many2one('hr.subcontract', 'Subcontract', ondelete='cascade', tracking=True)
    contract_type_id = fields.Many2one('hr.payroll.structure.type', 'Contract Type', tracking=True)

    def _prepare_allowance_vals(self):
        return {
            'code': self.code,
            'description': self.description,
            'amount': self.amount,
            'apply_on': self.apply_on,
            'contract_type_id': self.contract_type_id.id,
        }