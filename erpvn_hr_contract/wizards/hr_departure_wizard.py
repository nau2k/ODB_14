# -*- coding: utf-8 -*-
from odoo import _
from odoo.exceptions import UserError
from odoo.addons.hr_contract.wizard.hr_departure_wizard import HrDepartureWizard as OriginalHrDepartureWizard

def action_register_departure(self):
    """If set_date_end is checked, set the departure date as the end date to current running contract,
    and cancel all draft contracts"""
    current_contract = self.employee_id.contract_id
    if current_contract and current_contract.date_start > self.departure_date:
        raise UserError(_("Departure date can't be earlier than the start date of current contract."))
    super(OriginalHrDepartureWizard, self).action_register_departure()

    contracts_to_cancel = self.employee_id.contract_ids.filtered(lambda c: c.state == 'draft')
    contracts_to_cancel.write({'state': 'cancel'})
    contracts_to_end = (self.employee_id.contract_ids - contracts_to_cancel).filtered(lambda x: not x.date_end or x.date_end > self.departure_date)

    contracts_to_end.with_context(skip_update_expected_date=True).write({'date_end': self.departure_date, 'view_expected_end': True})
    contracts_to_end.mapped('subcontract_ids').with_context(skip_update_expected_date=True).write({'date_end': self.departure_date, 'view_expected_end': True})

OriginalHrDepartureWizard.action_register_departure = action_register_departure
