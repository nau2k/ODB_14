# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class WizardOptionPrintPy3o(models.TransientModel):
    _name = "wizard.option.print.py3o"
    _description = "Wizard Option Print Py3o"

    option_print = fields.Selection(
        string='Option print',
        selection=[('Subcontract', 'Print Subcontract'),
                   ('Contract', 'Print Contract'),
                   ],
                   default='Subcontract'
    )
    
    def print(self):
        for rec in self:
            info_subcontrac=self._context.get('info_subcontrac')
            ids =  self._context.get('subcontrac_id')
            url_str = '/web/binary/download_subcontract?model=hr.subcontract&field=data&id=%s&info=%s' % (ids,info_subcontrac)
            if rec.option_print == 'Contract':
                url_str = '/web/binary/download_contract?model=hr.subcontract&field=data&id=%s' % (ids)           
            return {
                'type' : 'ir.actions.act_url',
                'url': url_str,
                'target': 'self',
            }