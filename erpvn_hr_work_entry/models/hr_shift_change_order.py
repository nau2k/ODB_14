# -*- coding: utf-8 -*-
import pytz
from collections import defaultdict
from datetime import datetime, timedelta
from datetimerange import DateTimeRange
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_partner import _tz_get
from pytz import timezone, UTC

class HRShiftChangeOrder(models.Model):
    _name = 'hr.shift.change.order'
    _order = 'id desc'
    _description = "HR Shift Change Order"
    _inherit = 'mail.thread'

    @api.model
    def _get_default_shift(self):
        overtime_shift_ids = self.env['resource.calendar'].search([('is_overtime','!=',True)])
        if overtime_shift_ids:
            return overtime_shift_ids[0]
        return False

    name = fields.Char('Name', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', tracking=True)
    manager_id = fields.Many2one('hr.employee', string='Manager', related="department_id.manager_id", store=True)

    date_from = fields.Date(string='From', required=True, tracking=True)
    date_to = fields.Date(string='To', required=True, tracking=True)
    break_time = fields.Float(string='Break Time', compute='_compute_duration', store=True)
    duration = fields.Float(string='Period', compute='_compute_duration', store=True)
    work_entry_ids = fields.Many2many('hr.work.entry', 'shift_change_work_entry_rel', 'shift_change_id', 'work_entry_id', 'Work Entries')

    desc = fields.Text('Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Request'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')], string="State", default="draft", tracking=True)
    resource_calendar_id = fields.Many2one('resource.calendar', 'Working Shift', default=_get_default_shift, required=True, tracking=True)
    order_line_ids = fields.One2many('hr.shift.change.line', 'order_id', string='Overtime Lines')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    tz = fields.Selection(_tz_get, string='Timezone', required=True, default=lambda self: self.env.user.tz or 'UTC')

    @api.onchange('employee_id')
    def _onchange_employee(self):
        if self.employee_id and (not self.department_id or (self.department_id and self.department_id != self.employee_id.department_id)):
            self.department_id = self.employee_id.department_id

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('hr.shift.change.order') or '/'
        return super(HRShiftChangeOrder, self).create(values)

    @api.onchange('order_line_ids')
    def _onchange_overtime_lines(self):
        for rec in self.filtered(lambda x: x.order_line_ids):
            seq = 1
            for l in rec.order_line_ids:
                l.sequence = seq
                seq += 1

    def _prepare_new_work_entry_vals(self, line):
        self.ensure_one()
        return {
            'state': 'draft',
            'name': '-'.join([str(self.name), str(line.employee_id.name)]),
            'employee_id': line.employee_id.id,
            'attendance_id': line.attendance_id.id,
            'resource_calendar_id': line.resource_calendar_id.id,
            'work_entry_type_id': line.attendance_id.work_entry_type_id.id,
            'date_start': line.date_from,
            'date_stop': line.date_to,
            'break_time': line.break_time,
            'note': line.note,
            'tz': self.tz,
        }
    
    def action_approve(self):
        requests = self.filtered(lambda request: request.state == 'confirmed')
        if requests:
            if not requests.order_line_ids.filtered(lambda x: x.status == 'validation'):
                raise ValidationError(_("There is no validation line to change."))

            work_entry_obj = self.env['hr.work.entry'].sudo()
            # template_id = self.env.ref('erpvn_hr_overtime.mail_notify_about_approved_overtime_requests')
            # user_ids = self.env.ref('erpvn_hr_payroll.group_hr_payroll_manager').users

            # for record in requests:
                # ctx = defaultdict(list)
                # ctx['data'] = record.overtime_line_ids.filtered(lambda x: x.status == 'valid')
                # if user_ids and template_id:
                    # self.env['erpvn.base'].send_mail_template(record, template_id, user_ids, ctx)

            requests.write({'state': 'approved'})

            work_entry_vals = []
            for line in requests.order_line_ids.filtered(lambda x: x.status == 'validation'):
                work_entry_vals.append(line.order_id._prepare_new_work_entry_vals(line))

            requests.work_entry_ids.filtered(lambda x: x.state not in ['cancelled', 'conflict', 'validated']).write({'state': 'cancelled'})
            # create hr.work.entry...
            if work_entry_vals:
                work_entry_obj.create(work_entry_vals)

    def action_draft(self):
        overtime_requests = self.filtered(lambda request: request.state == 'cancelled')
        if overtime_requests:
            overtime_requests.write({'state': 'draft'})
            return True
        return False

    def action_confirm(self):
        overtime_requests = self.filtered(lambda request: request.state == 'draft')
        if overtime_requests:
            overtime_requests.write({'state': 'confirmed'})
            return True
        return False

    def action_cancel(self):
        overtime_requests = self.filtered(lambda request: request.state in ['draft', 'confirmed'])
        if overtime_requests:
            overtime_requests.write({'state': 'cancelled'})
            return True
        return False

    def _prepare_work_entry_vals(self, employee):
        base_obj = self.env['erpvn.base']
        tz = self.tz
        _employee_id = employee.sudo()
        results = []
        run_date = self.date_from
        while run_date <= self.date_to:
            datetime_from = datetime.combine(run_date, datetime.min.time()).replace(tzinfo=pytz.timezone(tz))
            datetime_to = datetime.combine(run_date, datetime.max.time()).replace(tzinfo=pytz.timezone(tz))
            # convert to UTC timezone to save to database.
            time_range = DateTimeRange(
                base_obj.convert_time_to_utc(datetime_from.replace(tzinfo=None), tz_name=tz).replace(tzinfo=None),
                base_obj.convert_time_to_utc(datetime_to.replace(tzinfo=None), tz_name=tz).replace(tzinfo=None)
            )

            calendar_id = self.resource_calendar_id
            intervals = calendar_id._attendance_intervals_batch(datetime_from, datetime_to, _employee_id.resource_id)
            existed_shifts = _employee_id.work_entry_ids.filtered(lambda x: x.state != 'cancelled' and x.date_start and x.date_stop and \
                            ((x.date_start > time_range.start_datetime and x.date_start < time_range.end_datetime) or \
                            (x.date_start <= time_range.start_datetime and x.date_stop > time_range.start_datetime)))
            
            existed_requests = self.env['hr.shift.change.line'].search([('employee_id', '=', _employee_id.id), ('state', '!=', 'cancelled')])\
                .filtered(lambda x: ((x.date_from > time_range.start_datetime and x.date_from < time_range.end_datetime) or \
                (x.date_from <= time_range.start_datetime and x.date_to > time_range.start_datetime)))
            for start, stop, meta in intervals[_employee_id.resource_id.id]:
                status = 'validation'
                dt_fr = base_obj.convert_time_to_utc(start.replace(tzinfo=None), tz_name=start.tzinfo.zone).replace(tzinfo=None)
                dt_to = base_obj.convert_time_to_utc(stop.replace(tzinfo=None), tz_name=stop.tzinfo.zone).replace(tzinfo=None)
                
                if existed_shifts:
                    validated_shifts = existed_shifts.filtered(lambda x: x.state == 'validated' and ((x.date_start > dt_fr and x.date_start < dt_to) or \
                                    (x.date_start <= dt_fr and x.date_stop > dt_fr)))
                    if validated_shifts:
                        status = 'validated-shift'

                if status == 'validation' and existed_requests:
                    duplicated_requests = existed_requests.filtered(lambda x: (x.date_from > dt_fr and x.date_to < dt_to) or (x.date_from <= dt_fr and x.date_to > dt_fr))
                    if duplicated_requests:
                        status = 'duplicated-request'
                    
                results.append((0, 0, {
                    'date_from': dt_fr,
                    'date_to': dt_to,
                    'resource_calendar_id': calendar_id.id,
                    'attendance_id': meta.id,
                    'employee_id': _employee_id.id,
                    'note': self.desc,
                    'status': status,
                }))

            if existed_shifts: 
                self.work_entry_ids |= existed_shifts

            run_date += timedelta(days=1)

        return results

    def compute_sheet(self):
        requests = self.filtered(lambda req: req.state == 'draft')
        if requests:
            for request in requests:
                self.order_line_ids = [(6, 0, [])]
                self.work_entry_ids = [(6, 0, [])]
                employee_ids = request.employee_id if request.employee_id else request.department_id.member_ids
                if not employee_ids:
                    continue
                
                employee_ids = employee_ids.sudo().filtered(lambda x: x.barcode and x.employee_type_id.name != 'Machine')
                work_entry_vals = [(5, 0, 0)]
                for employee in employee_ids:
                    work_entry_vals += request._prepare_work_entry_vals(employee)

                if work_entry_vals:
                    seq = 1
                    for val in work_entry_vals:
                        if val[0] != 0:
                            continue
                        if len(val) > 2:
                            val[2]['sequence'] = seq
                            seq += 1

                    request.with_context(compute_sheet=True).write({'order_line_ids': work_entry_vals})

