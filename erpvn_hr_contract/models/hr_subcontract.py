# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HRSubcontract(models.Model):
    _name = "hr.subcontract"
    _description = "HR Subcontract"
    _inherit = ['hr.contract']
    _order = 'create_date desc'

    sub_state = fields.Selection(selection=[('draft', 'New'), ('wait', 'Waiting'), ('run', 'Running'), ('end', 'Closed'), ('cancel', 'Cancelled')],
        string='Sub-Status', default='draft')
    contract_id = fields.Many2one('hr.contract', string='Contract')
    allowance_ids = fields.One2many('hr.contract.allowance', 'subcontract_id', 'Allowance')
    subcontract_info = fields.Selection(string='field_name',
        selection=[('salary', 'Print Salary'), ('Job', 'Print Job'), ('both', 'Print both')])

    @api.model
    def default_get(self, fields):
        res = super(HRSubcontract, self).default_get(fields)
        if self.env.context.get('default_contract_id'):
            contract_id = self.env['hr.contract'].browse(self.env.context['default_contract_id'])
            res['contract_id'] = contract_id.id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        return super(HRSubcontract, self.with_context(create_hr_subcontract=True)).create(vals_list)

    def action_confirm(self):
        for sub in self:
            sub.write({
                'sub_state': 'wait'
            })

    def action_approve(self):
        for sub in self:
            sub.write({
                'sub_state': 'run'
            })

    def action_end(self):
        for sub in self:
            sub.write({
                'sub_state': 'end'
            })

    def action_cancel(self):
        for sub in self:
            sub.write({
                'sub_state': 'cancel'
            })

    @api.constrains('employee_id', 'state', 'kanban_state', 'date_start', 'date_end')
    def _check_current_contract(self):
        if self._name != 'hr.subcontract':
            super(HRSubcontract, self)._check_current_contract()
    
    def print_option(self):
        self.ensure_one()
        form_view_id = self.env.ref('erpvn_hr_contract.print_option_form_view')
        
        return {
            'name': _('Open Option Print'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.option.print.py3o',
            'views': [(form_view_id.id, 'form')],
            'view_id': form_view_id.id,
            'target': 'new',
            'context':{'subcontrac_id':self.ids, 'info_subcontrac':self.subcontract_info}
        }
