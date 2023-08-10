# -*- coding: utf-8 -*-
from odoo import models, _


class User(models.Model):
    _inherit = "res.users"

    def action_hr_employee_holidays(self):
        return {
            'name': _('Time Off'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'hr.leave',
            'view_id': self.env.ref('hr_holidays.hr_leave_view_tree_my').id,
            'domain': [('employee_id.user_id', 'in', self.ids), ('holiday_status_id.allocation_type', '!=', 'no')],
        }
