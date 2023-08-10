# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class HRLeaveEmployeeList(models.Model):
    _name = "hr.leave.employee.list"
    _description = "HR Leave Employee List"

    @api.depends('employee_id')
    def _compute_employee_barcode(self):
        for record in self:
            record.barcode = record.employee_id.barcode if record.employee_id.barcode else ''

    sequence = fields.Integer(default=1, index=True)
    name = fields.Char('Description')
    hr_leave_id = fields.Many2one('hr.leave', string='Leave ID', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    barcode = fields.Char(compute='_compute_employee_barcode', string='Badge ID', store=True)
    hr_leave_type_id = fields.Many2one("hr.leave.type", store=True, string="Time Off Type",
        readonly=False, domain=[('valid', '=', True)])

    allocation_total_display = fields.Char(compute='_compute_allocation', store=True)
    allocation_remained_display = fields.Char(compute='_compute_allocation', store=True)
    allocation_taken_display = fields.Char(compute='_compute_allocation', store=True)

    request_date_from = fields.Date('Request Start Date')
    request_date_to = fields.Date('Request End Date')
    parent_id = fields.Many2one('hr.leave', string='Parent')
    date_from = fields.Datetime('Start Date')
    date_to = fields.Datetime('End Date')
    number_of_days = fields.Float('Duration (Days)')
    duration_display = fields.Char('Duration (Days/Hours)')
    number_of_hours = fields.Float('Hour(s)')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
        ], string='State')
    notes = fields.Text('Reasons')

    status = fields.Selection([('valid', 'Valid'), ('diff', 'Difference'),
        ('duplicated', 'Duplicated'), ('unwork', 'Unwork')], string='Status')

    @api.depends('employee_id')
    def _compute_allocation(self):
        annual_leave_id = self.env['hr.leave.type'].sudo().search([('code', '=', 'ANPL')], limit=1)

        for record in self:
            data_days = annual_leave_id.get_employees_days([record.employee_id.id])[record.employee_id.id]
            result = data_days.get(annual_leave_id.id, {})

            total = result.get('max_leaves', 0)
            taken = result.get('max_leaves', 0) - result.get('virtual_remaining_leaves', 0)
            remain = result.get('virtual_remaining_leaves', 0) if result.get('virtual_remaining_leaves', 0) > 0 else 0

            record.allocation_total_display = '%s:%s (hours)' % (int(total), round((total % 1) * 60))
            record.allocation_taken_display = '%s:%s (hours)' % (int(taken), round((taken % 1) * 60))
            record.allocation_remained_display = '%s:%s (hours)' % (int(remain), round((remain % 1) * 60))