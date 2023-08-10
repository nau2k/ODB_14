# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.osv import expression
# from odoo.tools.float_utils import float_round


class HRLeaveAllocation(models.Model):
	_inherit = 'hr.leave.allocation'

    # def _compute_remaining_leaves(self):
    #     for allocation in self:
    #         leaves = self.env['hr.leave'].search([
	# 			('employee_id', '=', allocation.employee_id.id),
	# 			('state', '=', 'validate'),
	# 			('holiday_status_id', '=',  allocation.holiday_status_id.id)
	# 		])
    #         allocation.remaining_leaves = allocation.number_of_days - sum(leaves.mapped('number_of_days'))
    
    # def _compute_remaining_leaves_display(self):
    #     for allocation in self:
    #         allocation.remaining_leaves_display = '%g %s' % (float_round(allocation.remaining_leaves, precision_digits=2), _('days'))

	remaining_leaves = fields.Float(string='Remaining Leaves',)# compute='_compute_remaining_leaves')
	remaining_leaves_display = fields.Char(string='Remaining (Days/Hours)',) # compute='_compute_remaining_leaves_display')

	# @api.model
	# def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
	# 	if self._context.get('search_default_hr_leave_allocation', False):
	# 		domain = [('create_uid', '=', self._uid)]

	# 		if self.env.user.employee_id:
	# 			domain = [('employee_id', '=', self.env.user.employee_id.id)]

	# 		# user has Responsible -> see all employee managed by him/her.
	# 		if self.env.user.has_group('hr_holidays.group_hr_holidays_responsible'):
	# 			domain = expression.OR([domain, [('employee_id', 'in', self.env.user.employee_id.child_ids.ids)]])

	# 		# user has All Approver -> see all.
	# 		if self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
	# 			domain = []
	# 		args = expression.AND([domain, args])
	# 	return super()._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)
