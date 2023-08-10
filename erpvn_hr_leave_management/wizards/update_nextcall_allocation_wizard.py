# -*- coding: utf-8 -*-
from odoo import fields, models, _


class UpdateNextcallAllocationWizard(models.TransientModel):
    _name = "update.nextcall.allocation.wizard"
    _description = "Update Nextcall Allocation Wizard"

    date = fields.Date(string="Start Date", required=True, default=fields.Date.context_today)

    def action_update(self):
        self.ensure_one()
        allocations = self.env['hr.leave.allocation'].browse(self._context.get('allocations', []))

        if allocations.filtered(lambda x: x.allocation_type != 'accrual'):
            message_id = self.env['message.wizard'].create({'message': _('This action only for Accrual Allocation')})
            return {
                'name': _('Notification'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                'res_id': message_id.id,
                'target': 'new',
            }

        allocations.filtered(lambda x: x.allocation_type == 'accrual').write({'nextcall': self.date})
        return {"type": "ir.actions.act_window_close"}