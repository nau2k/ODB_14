# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar
from odoo.osv import expression
from odoo import models, fields, api, _


class TimesheetAdjustmentRequestLine(models.Model):
    _name = 'timesheet.adjustment.request.line'
    _description = 'Timesheet Adjustment Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True)
    order_id = fields.Many2one('timesheet.adjustment.request', required=True)
    sequence = fields.Integer(default=1)
    employee_id = fields.Many2one('hr.employee', default=lambda self: self.env.user.employee_id, required=True, index=True, tracking=True)
    employee_code = fields.Char(related='employee_id.barcode', string='Badge ID', store=True)
    work_entry_id = fields.Many2one('hr.work.entry', string='Adjustment Entry', ondelete='cascade', store=True, required=True, tracking=True)
    work_entry_type_id = fields.Many2one('hr.work.entry.type', string='Entry Type', store=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Shift', store=True)
    attendance_id = fields.Many2one('resource.calendar.attendance', string='Work Detail', store=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('validated', 'Validated'), ('cancelled', 'Cancelled')], default='draft', tracking=True)
    note = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True, default=lambda self: self.env.company)

    old_date_start = fields.Datetime(store=True, string='Current From')
    old_date_stop = fields.Datetime(store=True, string='Current To')
    old_duration = fields.Float(store=True, string='Current Period')

    new_date_start = fields.Datetime(required=True, string='New From', tracking=True)
    new_date_stop = fields.Datetime(compute='_compute_new_date_stop', store=True, readonly=False, string='New To', tracking=True)
    new_duration = fields.Float(compute='_compute_new_duration', store=True, string='New Period', tracking=True)
    break_time = fields.Float(string='Break Time', readonly=True)
    

    @api.depends('new_date_stop', 'new_date_start')
    def _compute_new_duration(self):
        for request in self:
            request.new_duration = self._get_duration(request.new_date_start, request.new_date_stop)

    @api.depends('new_date_start', 'new_duration')
    def _compute_new_date_stop(self):
        for request in self.filtered(lambda x: x.new_date_start and x.new_duration):
            request.new_date_stop = request.new_date_start + relativedelta(hours=request.new_duration)

    def _get_duration(self, start, stop):
        if not start or not stop:
            return 0
        dt = stop - start
        return dt.days * 24 + dt.seconds / 3600

    @api.onchange('work_entry_id')
    def _onchange_work_entry(self):
        self.write({
            'work_entry_type_id': self.work_entry_id.work_entry_type_id.id,
            'resource_calendar_id': self.work_entry_id.resource_calendar_id.id,
            'attendance_id': self.work_entry_id.attendance_id.id,
            'old_date_start': self.work_entry_id.actual_start,
            'old_date_stop': self.work_entry_id.actual_stop,
            'old_duration': self.work_entry_id.actual_duration,
        })

    def action_set_to_draft(self):
        adjustment_requests = self.filtered(lambda x: x.state == 'cancelled')
        if adjustment_requests:
            adjustment_requests.write({'state': 'draft'})
            return True
        return False

    def change_duration_new_in_mail(self):
        duration = self.new_date_stop - self.new_date_start
        s = duration.total_seconds()
        m = divmod(s, 60)
        h = divmod(m[0], 60)
        d = '%s:%s' % (int(h[0]), int(h[1]))
        return d

    def change_duration_old_in_mail(self):
        s = self.old_duration * 60 * 60
        m = divmod(s, 60)
        h = divmod(m[0], 60)
        d = '%s:%s' % (int(h[0]), int(h[1]))
        return d

    def send_noti(self):
        template_id = self.env.ref('erpvn_hr_work_entry.approve_timesheet_adjustment_request_line_mail_template')
        template_id.send_mail(self.id)

    def action_confirm(self):
        adjustment_requests_to_confirm = self.filtered(lambda x: x.state == 'draft')
        if adjustment_requests_to_confirm:
            adjustment_requests_to_confirm.write({'state': 'confirm'})
            for i in adjustment_requests_to_confirm:
                i.send_noti()               
            return True
        return False

    def action_validate(self):
        adjustment_requests_to_validate = self.filtered(lambda x: x.state == 'confirm')
        if adjustment_requests_to_validate:
            work_entries_to_update = self.env['hr.work.entry'].sudo()
            attendance_vals = []
            for request in adjustment_requests_to_validate:
                attendance_vals.append({
                    'employee_id': request.employee_id.id,
                    'check_in': request.new_date_start,
                    'check_out': request.new_date_stop,
                })

            if attendance_vals:
                self.env['hr.attendance'].sudo().create(attendance_vals)
            
            work_entries_to_update |= adjustment_requests_to_validate.work_entry_id
            # reconfirm for work.entry.
            work_entries_to_update.action_set_to_draft()
            work_entries_to_update.action_confirm()
            adjustment_requests_to_validate.write({'state': 'validated'})
            return True
        return False

    def action_cancel(self):
        adjustment_requests_to_cancel = self.filtered(lambda x: x.state in ('draft', 'confirm'))
        if adjustment_requests_to_cancel:
            adjustment_requests_to_cancel.write({'state': 'cancelled'})
            return True
        return False

    @api.model
    def create(self, vals):
        if not vals.get('order_id', False):
            request_obj = self.env['timesheet.adjustment.request']  
            dt_now = datetime.now()
            num_of_days_in_month = calendar.monthrange(dt_now.year, dt_now.month)[1]
            request_id = request_obj.search([
                ('state', 'not in', ('validated', 'cancelled')),
                ('create_date', '>=', dt_now + relativedelta(day=1, hour=0, minute=0, second=0)),
                ('create_date', '<=', dt_now + relativedelta(day=num_of_days_in_month, hour=23, minute=59, second=59)),
            ], limit=1)
            if not request_id:
                request_id = request_obj.create({'name': 'Request for ' + dt_now.strftime("%B, %Y")})
            vals.update({'order_id': request_id.id})
        return super(TimesheetAdjustmentRequestLine, self).create(vals)

    # @api.model
    # def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
    #     if self._context.get('default_timesheet_adjustment_request_line', False):
    #         domain = [('create_uid', '=', self._uid)]

    #         if self.env.user.employee_id:
    #             domain = [('employee_id', '=', self.env.user.employee_id.id)]

    #         # user has Responsible -> see all employee managed by him/her.
    #         if self.env.user.has_group('hr_holidays.group_hr_holidays_responsible'):
    #             domain = expression.OR([domain, [('employee_id', 'in', self.env.user.employee_id.child_ids.ids)]])

    #         # user has All Approver -> see all.
    #         if self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
    #             domain = []
    #         args = expression.AND([domain, args])
    #     return super()._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)
