# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError



class WizardHRSubcontract(models.TransientModel):
    _inherit = "wizard.hr.subcontract"

    def create_hr_contract(self):
        self.ensure_one()
        form_view_id = self.env.ref('hr_contract.hr_contract_view_form', raise_if_not_found=False)
        # create a new contract
        # contract_vals = self.contract_id.copy_data()
        contract = self
        contract_vals = self._prepare_updating_contract_vals(contract)
        contract_name = self.name
        if self.name =='New':
            employee = self.employee_id
            prefix = 'LBC-'
            if self.contract_type_id.is_trial:
                prefix = 'PAC-'

            contract_name = prefix + str(employee.barcode) +'/' + fields.Date.today().strftime("%d%m%y")
            
        if self.env['hr.contract'].search_count([('name', '=', contract_name)]) > 0:
            raise ValidationError(_("Contract reference %s already exists, please check again") % (contract_name))
        
        self.name= contract_name
        contract_vals.update({
            'name': self.name,
            'state': 'draft',
            'date_start': self.date_start,
            'date_end': self.date_end,
            'resource_calendar_id':self.resource_calendar_id.id
        })
        wizard_id=self.env['hr.contract'].create(contract_vals)
        
        return {
            'name': _('Create Contract'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.contract',
            'views': [(form_view_id.id, 'form')],
            'view_id': form_view_id.id,
            'target': 'current',
            'res_id': wizard_id.id,
        }


