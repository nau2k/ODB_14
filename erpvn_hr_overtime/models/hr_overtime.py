# -*- coding: utf-8 -*-
import pytz
from collections import defaultdict
from datetime import datetime, timedelta
from datetimerange import DateTimeRange
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_partner import _tz_get

class HrOvertime(models.Model):
    _name = 'hr.overtime'
    _order = 'id desc'
    _description = "HR Overtime"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_overtime_shift(self):
        overtime_shift_ids = self.env['resource.calendar'].search([('is_overtime','=',True)])
        if overtime_shift_ids:
            return overtime_shift_ids[0]
        return False

    @api.depends('attendance_ids')
    def _compute_time_actual(self):
        self.actual_time = sum(self.attendance_ids.mapped('worked_hours'))

    def _get_attendance(self):
        for att in self:
            employee_ids = att.overtime_line_ids.mapped('employee_id').ids
            check_in = datetime.strptime(str(att.overtime_day) + " " + str(timedelta(hours = float(att.hour_from))), '%Y-%m-%d %H:%M:%S')
            check_out = datetime.strptime(str(att.overtime_day) + " " + str(timedelta(hours = float(att.hour_to))), '%Y-%m-%d %H:%M:%S')
            att.attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', 'in', employee_ids),
                ('check_in', '>=', check_in),
                ('check_out', '<=', check_out),
            ])

    name = fields.Char('Name', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', store=True, readonly=False,
        compute='_compute_from_overtime_type', tracking=True)
    employee_tag_id = fields.Many2one('hr.employee.category', string='Employee Tag', store=True,
        readonly=False, compute='_compute_from_overtime_type', tracking=True)
    manager_id = fields.Many2one('hr.employee', string="Manager", related="department_id.manager_id")

    date_from = fields.Datetime(string='From', tracking=True)
    date_to = fields.Datetime(string='To', tracking=True)
    break_time = fields.Float(string='Break Time', compute='_compute_duration', store=True)
    duration = fields.Float(string='Period', compute='_compute_duration', store=True)
    attendance_ids = fields.One2many(string='Attendances', comodel_name='hr.attendance', compute=_get_attendance)
    actual_time = fields.Float(string='Actual Time', compute='_compute_time_actual', store=True)
    overtime_type = fields.Selection([
        ('department', 'By Department'),
        ('emp_tag', 'By Employee Tag')],
        string='Overtime Mode', required=True, default='department',
        help="Allow to create Overtime in batchs:"
            "\n- By Department: all employees of the specified Department"
            "\n- By Employee Tag: all employees of the specific employee group category")
    desc = fields.Text('Description')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirmed', 'Request'),
            ('approved', 'Approved'),
            ('cancelled', 'Cancelled')
        ], string="State", default="draft", tracking=True)
    leave_id = fields.Many2one('hr.leave.allocation', string="Leave ID", tracking=True)
    attchd_copy = fields.Binary('Attach A File')
    attchd_copy_name = fields.Char('File Name', tracking=True)
    type = fields.Selection([('cash', 'Cash'), ('leave', 'leave')], default=lambda self: self.env.company.overtime_type, string="Type")
    work_entry_ids = fields.One2many('hr.work.entry', 'overtime_id', string='Work Entries')
    resource_calendar_id = fields.Many2one('resource.calendar', 'Working Shift', default=_get_default_overtime_shift, required=True, tracking=True)
    attendance_id = fields.Many2one('resource.calendar.attendance', string='Work Detail', store=True, compute='_compute_attendance')
    overtime_day = fields.Date(string='Overtime Day', default=fields.Date.context_today, required=True, tracking=True)
    
    hour_from = fields.Selection([
        ('0', '00:00'), ('0.25', '00:15'), ('0.5', '00:30'), ('0.75', '00:45'),
        ('1', '1:00'), ('1.25', '1:15'), ('1.5', '1:30'), ('1.75', '1:45'),
        ('2', '2:00'), ('2.25', '2:15'), ('2.5', '2:30'), ('2.75', '2:45'),
        ('3', '3:00'), ('3.25', '3:15'), ('3.5', '3:30'), ('3.75', '3:45'),
        ('4', '4:00'), ('4.25', '4:15'), ('4.5', '4:30'), ('4.75', '4:45'),
        ('5', '5:00'), ('5.25', '5:15'), ('5.5', '5:30'), ('5.75', '5:45'),
        ('6', '6:00'), ('6.25', '6:15'), ('6.5', '6:30'), ('6.75', '6:45'),
        ('7', '7:00'), ('7.25', '7:15'), ('7.5', '7:30'), ('7.75', '7:45'),
        ('8', '8:00'), ('8.25', '8:15'), ('8.5', '8:30'), ('8.75', '8:45'),
        ('9', '9:00'), ('9.25', '9:15'), ('9.5', '9:30'), ('9.75', '9:45'),
        ('10', '10:00'), ('10.25', '10:15'), ('10.5', '10:30'), ('10.75', '10:45'),
        ('11', '11:00'), ('11.25', '11:15'), ('11.5', '11:30'), ('11.75', '11:45'),
        ('12', '12:00'), ('12.25', '12:15'), ('12.5', '12:30'), ('12.75', '12:45'),
        ('13', '13:00'), ('13.25', '13:15'), ('13.5', '13:30'), ('13.75', '13:45'),
        ('14', '14:00'), ('14.25', '14:15'), ('14.5', '14:30'), ('14.75', '14:45'),
        ('15', '15:00'), ('15.25', '15:15'), ('15.5', '15:30'), ('15.75', '15:45'),
        ('16', '16:00'), ('16.25', '16:15'), ('16.5', '16:30'), ('16.75', '16:45'),
        ('17', '17:00'), ('17.25', '17:15'), ('17.5', '17:30'), ('17.75', '17:45'),
        ('18', '18:00'), ('18.25', '18:15'), ('18.5', '18:30'), ('18.75', '18:45'),
        ('19', '19:00'), ('19.25', '19:15'), ('19.5', '19:30'), ('19.75', '19:45'),
        ('20', '20:00'), ('20.25', '20:15'), ('20.5', '20:30'), ('20.75', '20:45'),
        ('21', '21:00'), ('21.25', '21:15'), ('21.5', '21:30'), ('21.75', '21:45'),
        ('22', '22:00'), ('22.25', '22:15'), ('22.5', '22:30'), ('22.75', '22:45'),
        ('23', '23:00'), ('23.25', '23:15'), ('23.5', '23:30'), ('23.75', '23:45')], string='Hour From', required=True, tracking=True)

    hour_to = fields.Selection([
        ('0', '00:00'), ('0.25', '00:15'), ('0.5', '00:30'), ('0.75', '00:45'),
        ('1', '1:00'), ('1.25', '1:15'), ('1.5', '1:30'), ('1.75', '1:45'),
        ('2', '2:00'), ('2.25', '2:15'), ('2.5', '2:30'), ('2.75', '2:45'),
        ('3', '3:00'), ('3.25', '3:15'), ('3.5', '3:30'), ('3.75', '3:45'),
        ('4', '4:00'), ('4.25', '4:15'), ('4.5', '4:30'), ('4.75', '4:45'),
        ('5', '5:00'), ('5.25', '5:15'), ('5.5', '5:30'), ('5.75', '5:45'),
        ('6', '6:00'), ('6.25', '6:15'), ('6.5', '6:30'), ('6.75', '6:45'),
        ('7', '7:00'), ('7.25', '7:15'), ('7.5', '7:30'), ('7.75', '7:45'),
        ('8', '8:00'), ('8.25', '8:15'), ('8.5', '8:30'), ('8.75', '8:45'),
        ('9', '9:00'), ('9.25', '9:15'), ('9.5', '9:30'), ('9.75', '9:45'),
        ('10', '10:00'), ('10.25', '10:15'), ('10.5', '10:30'), ('10.75', '10:45'),
        ('11', '11:00'), ('11.25', '11:15'), ('11.5', '11:30'), ('11.75', '11:45'),
        ('12', '12:00'), ('12.25', '12:15'), ('12.5', '12:30'), ('12.75', '12:45'),
        ('13', '13:00'), ('13.25', '13:15'), ('13.5', '13:30'), ('13.75', '13:45'),
        ('14', '14:00'), ('14.25', '14:15'), ('14.5', '14:30'), ('14.75', '14:45'),
        ('15', '15:00'), ('15.25', '15:15'), ('15.5', '15:30'), ('15.75', '15:45'),
        ('16', '16:00'), ('16.25', '16:15'), ('16.5', '16:30'), ('16.75', '16:45'),
        ('17', '17:00'), ('17.25', '17:15'), ('17.5', '17:30'), ('17.75', '17:45'),
        ('18', '18:00'), ('18.25', '18:15'), ('18.5', '18:30'), ('18.75', '18:45'),
        ('19', '19:00'), ('19.25', '19:15'), ('19.5', '19:30'), ('19.75', '19:45'),
        ('20', '20:00'), ('20.25', '20:15'), ('20.5', '20:30'), ('20.75', '20:45'),
        ('21', '21:00'), ('21.25', '21:15'), ('21.5', '21:30'), ('21.75', '21:45'),
        ('22', '22:00'), ('22.25', '22:15'), ('22.5', '22:30'), ('22.75', '22:45'),
        ('23', '23:00'), ('23.25', '23:15'), ('23.5', '23:30'), ('23.75', '23:45')], string='Hour To', required=True, tracking=True)
    
    overtime_line_ids = fields.One2many('hr.overtime.line', 'overtime_id', string='Overtime Lines')
    calendar_mismatch = fields.Boolean(compute='_compute_calendar_mismatch')
    mismatch_msg = fields.Char(store=True, compute='_compute_attendance')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    tz = fields.Selection(_tz_get, string='Timezone', required=True, default=lambda self: self.env.user.tz or 'UTC')

    @api.depends('overtime_type')
    def _compute_from_overtime_type(self):
        for record in self:
            if record.overtime_type == 'department':
                if not record.department_id:
                    record.department_id = self.env.user.employee_id.department_id
                record.employee_tag_id = False
            elif record.overtime_type == 'emp_tag':
                record.department_id = False
                if self.env.user.employee_id.category_ids:
                    record.employee_tag_id = self.env.user.employee_id.category_ids[0]
                else:
                    record.employee_tag_id = False

    @api.depends('resource_calendar_id', 'overtime_day')
    def _compute_calendar_mismatch(self):
        for record in self:
            record.calendar_mismatch = str(record.overtime_day.weekday()) not in record.resource_calendar_id.attendance_ids.mapped('dayofweek')

    @api.depends('calendar_mismatch')
    def _compute_attendance(self):
        for record in self:
            if record.calendar_mismatch:
                record.mismatch_msg = _('Mismatch: %s is %s. %s is not existed in Working Shift %s.') \
                    %(record.overtime_day.strftime('%B %d, %Y'), record.overtime_day.strftime('%A'), \
                        record.overtime_day.strftime('%A'), str(record.resource_calendar_id.name))
            else:
                record.mismatch_msg = ''

    @api.depends('hour_from', 'hour_to', 'overtime_day', 'resource_calendar_id')
    def _compute_duration(self):
        for record in self:
            record.duration = 0.0
            if record.hour_from and record.hour_to:

                from_datetime = datetime.combine(record.overtime_day, datetime.min.time()) + timedelta(hours=float(record.hour_from))
                to_datetime = datetime.combine(record.overtime_day, datetime.min.time()) + timedelta(hours=float(record.hour_to))

                period = float(record.hour_to) - float(record.hour_from)
                if float(record.hour_to) < float(record.hour_from):
                    period = 24.0 - float(record.hour_from) + float(record.hour_to)
                    to_datetime = datetime.combine(record.overtime_day, datetime.min.time()) + timedelta(days=1, hours=float(record.hour_to))
                
                local_tz = pytz.timezone(record.resource_calendar_id.tz)
                from_datetime = local_tz.localize(from_datetime)
                to_datetime = local_tz.localize(to_datetime)

                intervals = record.resource_calendar_id._attendance_intervals_batch(from_datetime, to_datetime, record.resource_calendar_id)

                break_time = 0.0
                for start, stop, meta in intervals[record.resource_calendar_id.id]:
                    break_duration = record.resource_calendar_id._get_breaking_hours(meta, start, stop)
                    if break_duration > 0.0:
                        break_time += break_duration

                if break_time > 0.0:
                    period -= break_time

                record.break_time = break_time
                record.duration = period

    def _get_non_duplicated_vals(self, work_entry_vals):
        results = []
        for att_id in set(map(lambda x: x['attendance_id'], work_entry_vals)):
            dicts_with_same_att = list(filter(lambda x: x['attendance_id'] == att_id, work_entry_vals))
            dicts_length = len(dicts_with_same_att)

            if dicts_length > 1:
                i = 0
                val = dicts_with_same_att[i]
                while i < dicts_length - 1:
                    next_val = dicts_with_same_att[i+1]
                    if (next_val['date_start'] - val['date_stop']).seconds == 1:
                        val['date_stop'] = next_val['date_stop']
                        val['break_time'] += next_val['break_time']
                        results.append(val)
                        i += 1
                    else:
                        results.append(val)
                        val = next_val
                    i += 1
            else:
                results.append(dicts_with_same_att[0])
        return results

    def _prepare_work_entry_vals(self, line):
        self.ensure_one()
        
        date_start_user_tz = datetime.combine(line.overtime_day, datetime.min.time()) + timedelta(hours=float(line.hour_from))
        date_stop_user_tz = date_start_user_tz + timedelta(hours=(line.duration + line.break_time))

        # add tzinfo to run func: _attendance_intervals_batch.
        local_tz = pytz.timezone(self.resource_calendar_id.tz)
        date_start_user_tz = local_tz.localize(date_start_user_tz)
        date_stop_user_tz = local_tz.localize(date_stop_user_tz)

        intervals = self.resource_calendar_id._attendance_intervals_batch(date_start_user_tz, date_stop_user_tz, self.resource_calendar_id)
        work_entry_vals = []

        for start, stop, meta in intervals[self.resource_calendar_id.id]:
            # set origin time.
            o_time_stop = stop.time().hour + stop.time().minute/60 + stop.time().second/3600
            o_date_stop = stop.date()

            run_time_start = start.time().hour + start.time().minute/60 + start.time().second/3600
            run_time_stop = stop.time().hour + stop.time().minute/60 + stop.time().second/3600

            run_date_start = start.date()
            run_date_stop = start.date()

            for att in meta:
                current_time_start = run_time_start
                current_time_stop = run_time_stop

                current_date_start = run_date_start
                current_date_stop = run_date_stop

                att_from = att.hour_from
                att_to = att.hour_to
                if att.dayofweek != att.dayofweek_to:
                    min_time = datetime.min.time().hour + datetime.min.time().minute/60
                    max_time = datetime.max.time().hour + datetime.max.time().minute/60 + datetime.max.time().second/3600
                    if str(current_date_start.weekday()) == att.dayofweek:
                        att_to = max_time
                    else:
                        att_from = min_time

                if att_from > current_time_start and att_to >= current_time_stop:
                    current_time_start = att_from
                elif att_from <= current_time_start and att_to < current_time_stop:
                    # convert 23:59 to 23:59:59s
                    if round(att_to, 4) == 23.9833:
                        att_to += datetime.max.time().second/3600
                    current_time_stop = att_to

                days = 0
                # allow overtime over one night only!
                if att.dayofweek != att.dayofweek_to and current_time_start > current_time_stop:
                    fr = int(att.dayofweek)
                    to = int(att.dayofweek_to)
                    days = to - fr
                    if days < 0:
                        days += 7
                current_date_stop += timedelta(days=days)

                dt_start = datetime.combine(current_date_start, datetime.min.time()) + timedelta(hours=current_time_start)
                dt_stop = datetime.combine(current_date_stop, datetime.min.time()) + timedelta(hours=current_time_stop)

                # update run time.
                run_time_start = current_time_stop
                run_time_stop = o_time_stop

                run_date_start = current_date_stop
                run_date_stop = o_date_stop

                break_time = 0.0
                break_duration = self.resource_calendar_id._get_breaking_hours(att, dt_start, dt_stop)
                if break_duration > 0.0:
                    break_time = break_duration

                work_entry_vals.append({
                    'state': 'draft',
                    'is_overtime': True,
                    'overtime_id': self.id,
                    'name': '-'.join([str(self.name), str(line.employee_id.name)]),
                    'employee_id': line.employee_id.id,
                    'attendance_id': att.id,
                    'resource_calendar_id': self.resource_calendar_id.id,
                    'work_entry_type_id': att.work_entry_type_id.id,
                    'overtime_line_id': line.id,
                    'date_start': local_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None),
                    'date_stop': local_tz.localize(dt_stop).astimezone(pytz.utc).replace(tzinfo=None),
                    'break_time': break_time,
                    'note': line.note,
                    'tz': local_tz.zone,
                })

        return self._get_non_duplicated_vals(work_entry_vals)

    def _get_update_ot_line_vals(self, lines_to_update):
        self.ensure_one()

        self = self.sudo()
        base_obj = self.env['erpvn.base']
        update_vales = []
        tz = self.tz

        for ot_line in lines_to_update:
            ot_date = ot_line.overtime_day
            _employee_id = ot_line.employee_id

            datetime_from = datetime.combine(ot_date, datetime.min.time()) + timedelta(hours=float(ot_line.hour_from))
            datetime_to = datetime_from + timedelta(hours=(ot_line.duration + ot_line.break_time))

            # get status depends on existed hr.overtime.line or hr.work.entry
            status = 'valid'

            # convert to UTC timezone to save to database.
            time_range = DateTimeRange(
                base_obj.convert_time_to_utc(datetime_from, tz_name=tz).replace(tzinfo=None),
                base_obj.convert_time_to_utc(datetime_to, tz_name=tz).replace(tzinfo=None)
            )

            employee_ot_lines = _employee_id.overtime_line_ids.filtered(lambda x: x.id != ot_line.id and x.overtime_id.id != self.id and \
                x.overtime_id.state != 'cancelled' and x.status == 'valid' and x.overtime_day == ot_date and x.hour_from and x.hour_to)

            if employee_ot_lines:
                for line in employee_ot_lines:
                    line_dt_from = base_obj.convert_time_to_utc(datetime.combine(ot_date, datetime.min.time()) \
                        + timedelta(hours=float(line.hour_from)), tz_name=tz).replace(tzinfo=None)
                    line_dt_to = base_obj.convert_time_to_utc(datetime.combine(ot_date, datetime.min.time()) \
                        + timedelta(hours=float(line.hour_to)), tz_name=tz).replace(tzinfo=None)

                    if float(line.hour_to) < float(line.hour_from):
                        line_dt_to = base_obj.convert_time_to_utc(datetime.combine(ot_date, datetime.min.time()) \
                            + timedelta(days=1, hours=float(line.hour_to)), tz_name=tz).replace(tzinfo=None)

                    line_ot_range = DateTimeRange(line_dt_from, line_dt_to)

                    # is_intersection return True even if 2 ranges continues
                    # so, we need to check that case with end_prev == start_next
                    if time_range.is_intersection(line_ot_range) and not (time_range.start_datetime == line_dt_to) and \
                        not (line_dt_from == time_range.end_datetime):
                        status = 'has-overtime'
                        break

            if status == 'valid':
                # is_intersection return True even if 2 ranges continues
                # so, we need to check that case with end_prev == start_next
                if _employee_id.work_entry_ids.filtered(lambda x: x.state != 'cancelled' and x.date_start and x.date_stop)\
                    .filtered(lambda y: time_range.is_intersection(DateTimeRange(y.date_start, y.date_stop)) and \
                        not (time_range.start_datetime == y.date_stop) and not (y.date_start == time_range.end_datetime)):
                    status = 'has-shift'
            

            update_vales.append((1, ot_line.id, {'status': status}))
        
        return update_vales


    def action_approve(self):
        overtime_requests = self.filtered(lambda request: request.state == 'confirmed')
        if overtime_requests:
            if not overtime_requests.overtime_line_ids.filtered(lambda x: x.status == 'valid'):
                raise ValidationError(_("There is no valid overtime line. So can not Approve."))

            work_entry_obj = self.env['hr.work.entry'].sudo()
            template_id = self.env.ref('erpvn_hr_overtime.mail_notify_about_approved_overtime_requests')
            user_ids = self.env.ref('erpvn_hr_payroll.group_hr_payroll_manager').users

            for record in overtime_requests:
                ctx = defaultdict(list)
                ctx['data'] = record.overtime_line_ids.filtered(lambda x: x.status == 'valid')
                if user_ids and template_id:
                    self.env['erpvn.base'].send_mail_template(record, template_id, user_ids, ctx)

            overtime_requests.write({'state': 'approved'})

            work_entry_vals = []
            for line in overtime_requests.overtime_line_ids.filtered(lambda x: x.status == 'valid'):
                work_entry_vals += line.overtime_id._prepare_work_entry_vals(line)

            # create hr.work.entry...
            if work_entry_vals:
                work_entry_obj.create(work_entry_vals)

    def action_draft(self):
        overtime_requests = self.filtered(lambda request: request.state == 'cancelled')
        if overtime_requests:
            overtime_requests.write({'state': 'draft'})
            for request in overtime_requests:
                line_vals = request._get_update_ot_line_vals(request.overtime_line_ids)
                if line_vals:
                    request.write({'overtime_line_ids': line_vals})
            return True
        return False

    def _check_if_error(self):
        if self.filtered(lambda x: x.calendar_mismatch):
            return True
        return False

    def action_confirm(self):
        overtime_requests = self.filtered(lambda request: request.state == 'draft')
        if overtime_requests:
            if overtime_requests._check_if_error():
                raise ValidationError('\n'.join(overtime_requests.filtered(lambda x: x.calendar_mismatch).mapped('mismatch_msg')))

            empty_note_line_ids = overtime_requests.overtime_line_ids.filtered(lambda x: x.status == 'valid' and (x.note and not x.note.strip() or not x.note))
            if empty_note_line_ids:
                raise ValidationError(_('Add note for these line(s):\n') + '\n'.join(empty_note_line_ids.mapped('employee_id.name')))

            for request in overtime_requests:
                if not request.overtime_line_ids.filtered(lambda x: x.status == 'valid'):
                    raise ValidationError(_("There is no valid overtime line. So can not Confirm."))
                
                if all(od_line != request.overtime_day for od_line in request.overtime_line_ids.mapped('overtime_day')):
                    raise ValidationError(_("Please make sure that you have clicked \"Load Employee\" button after changed Overtime Date on Overtime Order."))
                elif any(od_line != request.overtime_day for od_line in request.overtime_line_ids.mapped('overtime_day')):
                    diff_ot_date_lines = request.overtime_line_ids.filtered(lambda x: x.overtime_day != request.overtime_day)
                    raise ValidationError(_("List of Overtime Line(s) with different Date to the Overtime Order:\n\t+ %s") % '\t+ '.join(diff_ot_date_lines.mapped('display_name')))

            template_id = self.env.ref('erpvn_hr_overtime.mail_notify_for_approving_overtime_request')
            for record in overtime_requests:
                # reupdate invalid overtime lines last time before confirm overtime.
                line_vals = record._get_update_ot_line_vals(record.overtime_line_ids.filtered(lambda x: x.status != 'valid'))
                if line_vals:
                    record.write({'overtime_line_ids': line_vals})

                dict_val = defaultdict(lambda: self.env['hr.overtime.line'])
                for manager in record.department_id.manager_id:
                    dict_val[manager] = record.overtime_line_ids.filtered(lambda x: x.status == 'valid' and x.overtime_id.department_id.manager_id.id == manager.id)

                for manager in record.filtered(lambda x: not x.department_id):
                    manager = self.env.user.employee_id.department_id.manager_id
                    dict_val[manager] = record.overtime_line_ids.filtered(lambda x: x.status == 'valid' and not x.overtime_id.department_id)

                for manager, ot_lines in dict_val.items():
                    ctx = defaultdict(list)
                    ctx['data'] = ot_lines
                    user_ids = manager.user_id
                    if not user_ids:
                        user_ids = self.env.ref('erpvn_hr_payroll.group_hr_payroll_manager').users
                    if user_ids:
                        self.env['erpvn.base'].send_mail_template(record, template_id, user_ids, ctx)

            overtime_requests.write({'state': 'confirmed'})
            return True
        return False

    def action_cancel(self):
        overtime_requests = self.filtered(lambda request: request.state in ('draft', 'confirmed'))
        if overtime_requests:
            overtime_requests.write({'state': 'cancelled'})
            overtime_requests.overtime_line_ids.write({'status': 'cancel'})
            return True
        return False

    def _prepare_overtime_line_val(self, employee):
        base_obj = self.env['erpvn.base']
        tz = self.tz

        _employee_id = employee.sudo()
        
        datetime_from = datetime.combine(self.overtime_day, datetime.min.time()) + timedelta(hours=float(self.hour_from))
        datetime_to = datetime_from + timedelta(hours=(self.duration + self.break_time))

        # get status depends on existed hr.overtime.line or hr.work.entry
        status = 'valid'

        # convert to UTC timezone to save to database.
        time_range = DateTimeRange(
            base_obj.convert_time_to_utc(datetime_from, tz_name=tz).replace(tzinfo=None),
            base_obj.convert_time_to_utc(datetime_to, tz_name=tz).replace(tzinfo=None)
        )

        employee_ot_lines = _employee_id.overtime_line_ids.filtered(lambda x: x.overtime_id.id != self.id and \
            x.overtime_id.state != 'cancelled' and x.status == 'valid' and x.overtime_day == self.overtime_day and \
                x.hour_from and x.hour_to)

        if employee_ot_lines:
            for line in employee_ot_lines:
                line_dt_from = base_obj.convert_time_to_utc(datetime.combine(self.overtime_day, datetime.min.time()) \
                    + timedelta(hours=float(line.hour_from)), tz_name=tz).replace(tzinfo=None)
                line_dt_to = base_obj.convert_time_to_utc(datetime.combine(self.overtime_day, datetime.min.time()) \
                    + timedelta(hours=float(line.hour_to)), tz_name=tz).replace(tzinfo=None)

                if float(line.hour_to) < float(line.hour_from):
                    line_dt_to = base_obj.convert_time_to_utc(datetime.combine(self.overtime_day, datetime.min.time()) \
                        + timedelta(days=1, hours=float(line.hour_to)), tz_name=tz).replace(tzinfo=None)

                line_ot_range = DateTimeRange(line_dt_from, line_dt_to)

                # is_intersection return True even if 2 ranges continues
                # so, we need to check that case with end_prev == start_next
                if time_range.is_intersection(line_ot_range) and not (time_range.start_datetime == line_dt_to) and \
                    not (line_dt_from == time_range.end_datetime):
                    status = 'has-overtime'
                    break

        if status == 'valid':
            # is_intersection return True even if 2 ranges continues
            # so, we need to check that case with end_prev == start_next
            if _employee_id.work_entry_ids.filtered(lambda x: x.state != 'cancelled' and x.date_start and x.date_stop)\
                .filtered(lambda y: time_range.is_intersection(DateTimeRange(y.date_start, y.date_stop)) and \
                    not (time_range.start_datetime == y.date_stop) and not (y.date_start == time_range.end_datetime)):
                status = 'has-shift'
        
        return {
            'overtime_day': self.overtime_day,
            'hour_from': self.hour_from,
            'hour_to': self.hour_to,
            'duration': self.duration,
            'break_time': self.break_time,
            'employee_id': _employee_id.id,
            'note': self.desc,
            'status': status,
        }

    def compute_sheet(self):
        overtime_requests = self.filtered(lambda request: request.state in ('draft', 'confirmed'))
        if overtime_requests:
            employee_obj = self.env['hr.employee']
            for request in overtime_requests:
                employee_ids = employee_obj
                overtime_type = request.overtime_type

                if overtime_type == 'department':
                    employee_ids = request.department_id.member_ids
                elif overtime_type == 'emp_tag':
                    employee_ids = request.employee_tag_id.employee_ids
                
                employee_ids = employee_ids.sudo().filtered(lambda x: x.barcode and x.employee_type_id.name != 'Machine')
                overtime_line_vals = [(5, 0, 0)] + [(0, 0, request._prepare_overtime_line_val(employee)) for employee in employee_ids]

                if overtime_line_vals:
                    seq = 1
                    for val in overtime_line_vals:
                        if val[0] != 0:
                            continue
                        if len(val) > 2:
                            val[2]['sequence'] = seq
                            seq += 1

                    overtime_requests.with_context(compute_sheet=True).write({'overtime_line_ids': overtime_line_vals})

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('hr.overtime') or '/'
        return super(HrOvertime, self).create(values)

    def unlink(self):
        if self.filtered(lambda overtime: overtime.state != 'draft'):
            raise UserError(_('You cannot delete TIL request which is not in draft state.'))
        return super(HrOvertime, self).unlink()

    @api.model
    def _cancel_hr_overtime(self):
        seven_days_before_today = self.sudo().env.ref('erpvn_hr_overtime.ir_cron_cancel_overtime_request').nextcall - timedelta(days=7)
        hr_overtime_ids = self.env['hr.overtime'].search([('state', 'in', ['draft', 'confirmed']), ('create_date', '<=', seven_days_before_today)])
        hr_overtime_ids.action_cancel()
    
    def get_department(self):
        for rec in self:
            if rec.overtime_type=="department":
                return '- Department' + ' ' + rec.department_id.name
            return ''
        
    def update_num_sequence(self):
        for record in self:
            seq = 1
            for r in record.overtime_line_ids:
                r.sequence = seq
                seq += 1

    @api.onchange('overtime_line_ids')
    def _onchange_overtime_lines(self):
        for rec in self.filtered(lambda x: x.overtime_line_ids):
            seq = 1
            for l in rec.overtime_line_ids:
                l.sequence = seq
                seq += 1
