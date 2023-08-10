# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.exceptions import UserError
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from datetimerange import DateTimeRange
from collections import defaultdict
from pytz import timezone, UTC
import calendar, pytz

HOLIDAY_CODES = [
    'NDPL', # National Day/Ngày Quốc Khánh 2/9
    'IWDPL', # International Workers’ Day/Ngày Quốc tế Lao động 01/05
    'LBPL', # Liberation Day/Ngày Giải phóng miền Nam 30/04
    'LNPL', # Lunar New Year/Tết Nguyên đán
    'NYPL', # New Year/Tết Dương lịch
    'HKPL', # Hung Kings’ Day/Giỗ Tổ Hùng Vương
]

class HrWorkEntry(models.Model):
    _name = 'hr.work.entry'
    _inherit = ['hr.work.entry', 'mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'

    name = fields.Char(tracking=True)
    employee_id = fields.Many2one(tracking=True)
    date_start = fields.Datetime(tracking=True)
    date_stop = fields.Datetime(tracking=True)
    duration = fields.Float(tracking=True)
    work_entry_type_id = fields.Many2one(tracking=True)
    state = fields.Selection(selection_add=[('confirmed', 'Confirmed')], ondelete={'confirmed': 'cascade'}, tracking=True)
    employee_code = fields.Char(related='employee_id.barcode', string='Badge ID', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Department', store=True)
    employee_type_id = fields.Many2one(comodel_name='hr.employee.type', 
        string='Employee Type', related='employee_id.employee_type_id', store=True)
        
    actual_start = fields.Datetime(store=True, string='Actual From')
    actual_stop = fields.Datetime(store=True, string='Actual To')
    break_time = fields.Float(store=True, string="Break Time", tracking=True)
    actual_duration = fields.Float(store=True, string='Actual Period', compute='_compute_actual_duration', digits=(10,2))
    resource_calendar_id = fields.Many2one("resource.calendar",  "Working Shift", required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=True)
    attendance_id = fields.Many2one("resource.calendar.attendance", string="Work Detail",
        tracking=True, ondelete="restrict", required=True)
    tz = fields.Selection(_tz_get, string='Timezone', required=True, default=lambda self: self.env.user.tz or 'UTC')
    hr_attendance_ids = fields.Many2many(string='Attendances', comodel_name='hr.attendance',
        relation='work_entry_hr_attendacne_rel', column1='work_entry_id', column2='attendance_id')
    adjustment_request_ids = fields.One2many('timesheet.adjustment.request.line', 'work_entry_id', string='Adjustment Requests')
    rule_code = fields.Char(string="Rule Code")
    has_shift_adjustment_request = fields.Boolean(string='Has Shift Adjustment Request')

    # flexible time
    lack_hours= fields.Float('Lack Aft. Hours', compute='_compute_actual_duration', store=True, digits=(10,5))
    lack_bef_hours= fields.Float('Lack Bef. Flex', digits=(10,5))
    flex_hours= fields.Float('Flex Hours', digits=(10,5))
    is_flexible_time = fields.Boolean(string="Flexible Time", tracking=True)
    flex_hour_from = fields.Float(string='Flexible From', tracking=True)
    flex_hour_to = fields.Float(string='Flexible To', tracking=True)
    flex_hour_out = fields.Float(string='Flexible Out', tracking=True)
    flex_hour_limit_out = fields.Float(string='Flexible Limit Out', tracking=True)
     
    contract_id = fields.Many2one('hr.contract', string='Contract')
    note = fields.Text('Note')
    is_late = fields.Boolean(string='Is Late?', default=False)
    attendance_late = fields.Integer(string="Late (Minutes)", default=0.0, readonly=True)

    def _compute_lack_hour(self):
        result = self.duration - self.actual_duration
        if result < 0.0 or not (self.actual_start and self.actual_stop):
            result = 0.0
        return result

    # default, when cancel work entry it also set active=False.
    # def action_cancel(self):
    #     self.filtered(lambda x: x.state in ('draft', 'conflict')).write({'state': 'cancelled'})
    #     return True


    @api.onchange('attendance_id')
    def _onchange_attendance(self):
        if self.attendance_id.calendar_id:
            self.resource_calendar_id = self.attendance_id.calendar_id
        if self.attendance_id.work_entry_type_id:
            self.work_entry_type_id = self.attendance_id.work_entry_type_id
        if self.attendance_id.break_time_ids:
            self.break_time = sum(self.attendance_id.break_time_ids.mapped('duration'))

    @api.depends('actual_start', 'actual_stop', 'break_time')
    def _compute_actual_duration(self):
        for work_entry in self:
            work_entry.actual_duration = work_entry._get_actual_duration(work_entry.actual_start, work_entry.actual_stop)
            work_entry.lack_hours = work_entry._compute_lack_hour()

    # @api.depends('actual_start', 'actual_duration', 'break_time')
    # def _compute_actual_stop(self):
    #     for work_entry in self.filtered(lambda w: w.actual_start and w.actual_duration):
    #         work_entry.actual_stop = work_entry.actual_start + relativedelta(hours=work_entry.actual_duration + work_entry.break_time)

    def _get_breaking_hours(self, break_id, ac_start_float, ac_stop_float):
        break_duration = 0.0
        if ac_start_float <= break_id.hour_from and ac_stop_float >= break_id.hour_to:
            break_duration = break_id.duration
        elif ac_start_float > break_id.hour_from and ac_stop_float >= break_id.hour_to and break_id.hour_to > ac_start_float:
            break_duration = break_id.hour_to - ac_start_float
        elif ac_start_float <= break_id.hour_from and ac_stop_float < break_id.hour_to and ac_stop_float > break_id.hour_from:
            break_duration = ac_stop_float - break_id.hour_from
        return break_duration

    def _get_actual_duration(self, actual_start, actual_stop):
        if not actual_start or not actual_stop:
            return 0.0
        actual_duration = super(HrWorkEntry, self)._get_duration(actual_start, actual_stop)
        if self.break_time > 0.0:

            base_obj = self.env['erpvn.base']
            tz = self.tz

            start_time_tz = base_obj.convert_utc_time_to_tz(actual_start, tz).time()
            start_float = start_time_tz.hour + start_time_tz.minute/60.0

            stop_time_tz = base_obj.convert_utc_time_to_tz(actual_stop, tz).time()
            stop_float = stop_time_tz.hour + stop_time_tz.minute/60.0

            break_total = 0.0
            for break_id in  self.attendance_id.break_time_ids:
                break_total += self._get_breaking_hours(break_id, start_float, stop_float)

            if break_total:
                actual_duration -= break_total

        return actual_duration

    # Overriding
    @api.depends('date_start', 'duration', 'break_time')
    def _compute_date_stop(self):
        for work_entry in self.filtered(lambda w: w.date_start and w.duration):
            work_entry.date_stop = work_entry.date_start + relativedelta(hours=work_entry.duration + work_entry.break_time)

    @api.depends('date_stop', 'date_start', 'break_time')
    def _compute_duration(self):
        super(HrWorkEntry, self)._compute_duration()

    # Overloading
    def _get_duration(self, date_start, date_stop):
        if not date_start or not date_stop:
            return 0.0
        return super(HrWorkEntry, self)._get_duration(date_start, date_stop) - self.break_time

    def _get_related_attendances(self, attendances, date_start, date_stop, timezone):
        base_obj = self.env['erpvn.base']
        results = self.env['hr.attendance']
        for attendance in attendances:
            flag = False
            if attendance.check_in:
                flag = base_obj.convert_utc_time_to_tz(attendance.check_in, timezone).replace(tzinfo=None).date() in [date_start.date(), date_stop.date()]
            if not flag and attendance.check_out:
                flag = base_obj.convert_utc_time_to_tz(attendance.check_out, timezone).replace(tzinfo=None).date() in [date_start.date(), date_stop.date()]
            if flag:
                results |= attendance
        return results

    def _get_valid_range(self, atts):
        use_flexible = True
        attendances = atts.filtered(lambda x: x.check_in < x.check_out and not (x.check_out <= self.date_start or x.check_in >= self.date_stop))

        if len(attendances) > 1:
            dt_in, dt_out = False, False
            max_lst = []
            for att in attendances.sorted(lambda x: x.check_in):
                if dt_in and dt_out:
                    min_in = att.check_in
                    if list(filter(lambda x: x > min_in,  sorted(max_lst, reverse=True))):
                        min_in = list(filter(lambda x: x > min_in,  sorted(max_lst, reverse=True)))[0]

                    if min_in < dt_out:
                        min_in = dt_out

                    max_out = att.check_out 
                    if att.check_out >= self.date_stop:
                        max_out = self.date_stop
                        
                    dt_out = max_out - (min_in - dt_out)

                if not dt_in:
                    dt_in = att.check_in
                    if att.check_in <= self.date_start:
                        dt_in = self.date_start

                if not dt_out:
                    s = att.check_out
                    dt_out = att.check_out
                    if att.check_out <= self.date_start:
                        dt_in = self.date_start

                if att.check_out < self.date_stop:
                    max_lst.append(att.check_out)

            if not (dt_in <= self.date_start and dt_out >= self.date_stop):
                use_flexible = False

            return DateTimeRange(dt_in, dt_out), use_flexible

        if attendances.filtered(lambda x: x.check_in > self.date_start and x.check_out > self.date_stop):
            res = attendances.filtered(lambda x: x.check_in > self.date_start and x.check_out > self.date_stop)[0]
            return DateTimeRange(res.check_in, self.date_stop), use_flexible
        elif attendances.filtered(lambda x: x.check_in < self.date_start and x.check_out < self.date_stop):
            res = attendances.filtered(lambda x: x.check_in < self.date_start and x.check_out < self.date_stop)[0]
            return DateTimeRange(self.date_start, res.check_out), use_flexible
        elif attendances.filtered(lambda x: x.check_in == self.date_start and x.check_out < self.date_stop):
            res = attendances.filtered(lambda x: x.check_in == self.date_start and x.check_out < self.date_stop)[0]
            return DateTimeRange(self.date_start, res.check_out), use_flexible
        elif attendances.filtered(lambda x: x.check_in > self.date_start and x.check_out == self.date_stop):
            res = attendances.filtered(lambda x: x.check_in > self.date_start and x.check_out == self.date_stop)[0]
            return DateTimeRange(res.check_in, self.date_stop), use_flexible
        elif attendances.filtered(lambda x: x.check_in > self.date_start and x.check_out < self.date_stop):
            res = attendances.filtered(lambda x: x.check_in > self.date_start and x.check_out < self.date_stop)[0]
            return DateTimeRange(res.check_in, res.check_out), use_flexible
        return False, use_flexible

    def _get_update_vals(self, valid_range):
        # work_entry:  24/03/2022 17:00:00 - 24/03/2022 22:00:00
        # valid_range: 24/03/2022 07:21:26 - 24/03/2022 16:32:38
        vals = {
            'actual_start': self.date_start,
            'actual_stop': self.date_stop,
        }
        if valid_range.start_datetime > self.date_start:
           vals.update({'actual_start': valid_range.start_datetime})
        if valid_range.end_datetime < self.date_stop:
            vals.update({'actual_stop': valid_range.end_datetime})

        # check valid: 24/03/2022 16:32:38 < 24/03/2022 22:00:00
        actual_start = vals.get('actual_start') if 'actual_start' in vals else self.date_start
        actual_stop = vals.get('actual_stop') if 'actual_stop' in vals else self.date_stop
        if 'actual_start' in vals:
            if vals.get('actual_start') > actual_stop:
                del vals['actual_start']
        if 'actual_stop' in vals:
            if vals.get('actual_stop') < actual_start:
                del vals['actual_stop']
        return vals


    def _get_valid_attendances(self, work_entry):
        erpvn_base_obj = self.env['erpvn.base']
        hr_attendance_obj = self.env['hr.attendance']
        user_tz_start = erpvn_base_obj.convert_utc_time_to_tz(work_entry.date_start, work_entry.tz).replace(tzinfo=None)
        user_tz_stop = erpvn_base_obj.convert_utc_time_to_tz(work_entry.date_stop, work_entry.tz).replace(tzinfo=None)

        # Asian/Ho Chi Minh tz    UTC tz
        # 6:55 03/18/2022         23:55 03/17/2022
        # so, utc_hours_range must be:
        # 00:00:00 03/17/2022 -> 23:59:59 03/19/2022
        utc_hours_range = DateTimeRange(work_entry.date_start - timedelta(days=1) + relativedelta(hour=0, minute=0, second=0),
            work_entry.date_stop + timedelta(days=1) + relativedelta(hour=23, minute=59, second=59))
        related_attendance_ids = hr_attendance_obj.search([
            ('employee_id', '=', work_entry.employee_id.id), '|', '&',
            ('check_in', '>=', utc_hours_range.start_datetime), ('check_in', '<=', utc_hours_range.end_datetime), '&',
            ('check_out', '>=', utc_hours_range.start_datetime), ('check_out', '<=', utc_hours_range.end_datetime)
        ])

        # get related attendances for this work entry.
        attendances_in_same_date = self._get_related_attendances(related_attendance_ids, user_tz_start, user_tz_stop, work_entry.tz)
        # work_entry.write({'hr_attendance_ids': [(6, 0, attendances_in_same_date.ids)]})

        # change to user timezone then compare with user timezone of datetime in current work.entry.
        valid_range_attendances = related_attendance_ids.filtered_domain([('worked_hours', '>', 0.0),
            ('check_in', '>=', utc_hours_range.start_datetime), ('check_in', '<=', utc_hours_range.end_datetime),
            ('check_out', '>=', utc_hours_range.start_datetime), ('check_out', '<=', utc_hours_range.end_datetime)
        ])

        # attendance.check_in in [work.start_date(), work.stop_date()] or attendance.check_out in [work.start_date(), work.stop_date()]
        valid_attendance_ids = valid_range_attendances.filtered(lambda x: erpvn_base_obj.convert_utc_time_to_tz(x.check_in, work_entry.tz).replace(tzinfo=None).date() in [user_tz_start.date(), user_tz_stop.date()] or \
            erpvn_base_obj.convert_utc_time_to_tz(x.check_out, work_entry.tz).replace(tzinfo=None).date() in [user_tz_start.date(), user_tz_stop.date()])\
                .sorted(lambda re: re.worked_hours, reverse=True)

        return attendances_in_same_date, valid_attendance_ids

    def get_late_minutes(self, attendances_ids):
        attendance_late = 0.0
        if attendances_ids:
            week_day = attendances_ids.sorted('check_in')[0].sudo().check_in.weekday()
            if self.employee_id.contract_id:
                work_schedule = attendances_ids.sorted('check_in')[0].sudo().employee_id.contract_id.resource_calendar_id
                if self.resource_calendar_id == work_schedule:
                    for schedule in work_schedule.sudo().attendance_ids:
                        if schedule.dayofweek == str(week_day) and schedule.day_period == 'morning':
                            work_from = schedule.hour_from
                            result = '{0:02.0f}:{1:02.0f}'.format(*divmod(work_from * 60, 60))

                            user_tz = self.env.user.tz
                            dt = attendances_ids.sorted('check_in')[0].check_in

                            if user_tz in pytz.all_timezones:
                                old_tz = pytz.timezone('UTC')
                                new_tz = pytz.timezone(user_tz)
                                dt = old_tz.localize(dt).astimezone(new_tz)
                            str_time = dt.strftime("%H:%M")
                            check_in_date = datetime.strptime(str_time, "%H:%M").time()
                            start_date = datetime.strptime(result, "%H:%M").time()
                            t1 = timedelta(hours=check_in_date.hour, minutes=check_in_date.minute)
                            t2 = timedelta(hours=start_date.hour, minutes=start_date.minute)
                            if check_in_date > start_date:
                                final = t1 - t2
                                attendance_late = final.total_seconds() / 60
        return attendance_late

    def action_set_to_draft(self):
        # work_entries = self.filtered(lambda x: x.state in ('cancelled', 'confirmed'))
        if not self._check_if_error():
            for work_entry in self:
                work_entry.update({
                    'state': 'draft',
                    'actual_start': False,
                    'actual_stop': False,
                    'lack_hours': 0.0,
                    'lack_bef_hours': 0.0,
                    'flex_hours': 0.0,
                    'actual_duration': 0.0,
                    'hr_attendance_ids': [(6, 0, [])],
                })
            return True
        return False

    def action_confirm(self):
        work_entries = self.filtered(lambda x: x.state == 'draft')
        if not work_entries._check_if_error():
            for work_entry in work_entries:
                if work_entry.attendance_id.no_fingerprint_required:
                    work_entry.update({
                        'actual_start': work_entry.date_start,
                        'actual_stop': work_entry.date_stop,
                        'state': 'confirmed',
                    })
                    continue
                
                attendances_in_same_date, valid_attendance_ids = self._get_valid_attendances(work_entry)
                val = {
                    'hr_attendance_ids': [(6, 0, attendances_in_same_date.ids)],
                    'attendance_late': self.get_late_minutes(attendances_in_same_date),
                }
                if valid_attendance_ids:
                    if valid_attendance_ids.filtered(lambda x: x.worked_hours >= work_entry.duration \
                        and x.check_in <= work_entry.date_start and x.check_out >= work_entry.date_stop):

                        val.update({
                            'actual_start': work_entry.date_start,
                            'actual_stop': work_entry.date_stop,
                            'state': 'confirmed'
                        })
                        work_entry.update(val)
                        continue

                    valid_attendance_ids = valid_attendance_ids.filtered(lambda x: not ((x.check_out <= work_entry.date_start and x.check_out >= x.check_in) or (x.check_in >= work_entry.date_stop and x.check_out >= x.check_in)))
                    if not valid_attendance_ids:
                        continue

                    valid_range, use_flexible = work_entry._get_valid_range(valid_attendance_ids)
                    if not valid_range:
                        continue

                    if valid_range and valid_range.is_valid_timerange():
                        vals = work_entry._get_update_vals(valid_range)
                        if vals:
                            val.update({
                                'actual_start': vals['actual_start'],
                                'actual_stop': vals['actual_stop'],
                                'state': 'confirmed',
                            })

                    work_entry.update(val)
                    work_entry.actual_duration = work_entry._get_actual_duration(work_entry.actual_start, work_entry.actual_stop)
                    work_entry.lack_bef_hours = work_entry._compute_lack_hour()

                    if float_compare(work_entry.lack_hours, 0, precision_digits=3) == 1 and work_entry.is_flexible_time and use_flexible:
                        flex_dt_from = timezone(work_entry.tz).localize(datetime.combine(work_entry.date_start.date(), 
                            float_to_time(work_entry.flex_hour_from))).astimezone(UTC).replace(tzinfo=None)
                        flex_dt_to = timezone(work_entry.tz).localize(datetime.combine(work_entry.date_start.date(), 
                            float_to_time(work_entry.flex_hour_to))).astimezone(UTC).replace(tzinfo=None)
                        flex_dt_out = timezone(work_entry.tz).localize(datetime.combine(work_entry.date_start.date(), 
                            float_to_time(work_entry.flex_hour_out))).astimezone(UTC).replace(tzinfo=None)
                        flex_dt_limit_out = timezone(work_entry.tz).localize(datetime.combine(work_entry.date_start.date(), 
                            float_to_time(work_entry.flex_hour_limit_out))).astimezone(UTC).replace(tzinfo=None)

                        if work_entry.actual_start > flex_dt_from and work_entry.actual_start <= flex_dt_to:
                            late_hours = (work_entry.actual_start - work_entry.date_start).total_seconds() / 3600
                            attendance_to_checks = valid_attendance_ids.filtered(lambda x: x.check_out.date() == flex_dt_out.date() and \
                                                    x.check_out <= flex_dt_limit_out and x.check_out > flex_dt_out)
                            if attendance_to_checks:
                                check_out = max(attendance_to_checks.mapped('check_out'))
                                over_hours = (check_out - flex_dt_out).total_seconds() / 3600
                                if float_compare(over_hours, late_hours, precision_digits=3) != -1:
                                    work_entry.write({
                                        'actual_start': work_entry.date_start,
                                        'actual_stop': work_entry.date_stop,
                                        'flex_hours': late_hours,
                                    })
                                else:
                                    new_out = work_entry.actual_stop + timedelta(hours=over_hours)
                                    new_in = work_entry.actual_start - timedelta(hours=over_hours)
                                    vals = {'flex_hours': over_hours}
                                    if new_out <= work_entry.date_stop:
                                        vals['actual_stop'] = new_out
                                    elif new_in >= work_entry.date_start:
                                        vals['actual_start'] = new_in
                                    else:
                                        flex_tail = (work_entry.date_stop - work_entry.actual_stop).total_seconds() / 3600
                                        flex_head = over_hours - flex_tail
                                        vals['actual_stop'] = work_entry.date_stop
                                        if flex_head > 0:
                                            vals['actual_start'] = work_entry.actual_start - timedelta(hours=flex_head)
                                    work_entry.write(vals)

            return True
        return False


    def action_fix_attendance(self):
        work_entries = self.filtered(lambda x: x.state in ['draft', 'confirmed'] and not x.is_overtime)
        if work_entries:
            for w in work_entries:
                if len(w.hr_attendance_ids) > 1 and w.actual_duration != w.duration:
                    time_lst = w.hr_attendance_ids.filtered(lambda x: x.state not in ['cancelled', 'no_check_out'] and x.check_in).mapped('check_in') + \
                        w.hr_attendance_ids.filtered(lambda x: x.state not in ['cancelled', 'no_check_in'] and x.check_out).mapped('check_out')
                    if len(time_lst) > 1:
                        time_lst.sort()

                        dt_min = time_lst[0]
                        dt_max = time_lst[-1]
                        
                        i = -1
                        while dt_max and ((dt_max - dt_min).total_seconds() / 3600) < 12:
                            i -= 1
                            dt_max = time_lst[i]
                            if dt_max == dt_min:
                                dt_max = False
                                break

                        if not dt_max:
                            continue

                        w.hr_attendance_ids[0].write({
                            'check_in': dt_min,
                            'check_out': dt_max,
                            'state': 'draft',
                        })

                        ignore_time_lst = [dt_min, dt_max]
                        for a in w.hr_attendance_ids[1:]:
                            count = 0
                            a.write({'check_in': False, 'check_out': False, 'state': 'draft'})
                            for t in time_lst:
                                if t in ignore_time_lst:
                                    continue

                                count += 1
                                if count == 1:
                                    ignore_time_lst.append(t)
                                    a.write({'check_in': t})
                                elif count == 2:
                                    ignore_time_lst.append(t)
                                    a.write({'check_out': t})
                                else:
                                    break

                    w.action_confirm()
            return True
        return False

    def action_validate(self):
        work_entries = self.filtered(lambda x: x.state == 'confirmed')
        return super(HrWorkEntry, work_entries).action_validate()

    def action_cancel(self):
        work_entry_requests = self.filtered(lambda request: request.state in ('draft', 'validated'))
        if work_entry_requests:
            work_entry_requests.write({'state': 'cancelled'})
            return True
        return False

    def action_fix_attendance_multi(self):
        work_entries = self.filtered(lambda work_entry: work_entry.state in ('draft', 'confirmed'))
        if not work_entries._check_if_error():
            work_entries.action_fix_attendance()

    def action_set_to_draft_multi(self):
        work_entries = self.filtered(lambda x: x.state not in ('conflict', 'cancelled', 'draft'))
        if not work_entries._check_if_error():
            work_entries.action_set_to_draft()

    def action_confirm_multi(self):
        work_entries = self.filtered(lambda work_entry: work_entry.state == 'draft')
        if not work_entries._check_if_error():
            work_entries.action_confirm()

    def action_validate_multi(self):
        work_entries = self.filtered(lambda work_entry: work_entry.state == 'confirmed')
        if not work_entries._check_if_error():
            work_entries.action_validate()

    def make_adjustment_request(self):
        wz_id =  self.env['wizard.timesheet.adjustment.request'].create({
            'name':'Timesheet adjustment request',
        })

        request_obj = self.env['timesheet.adjustment.request']
        request_line_obj = self.env['wizard.timesheet.adjustment.request.line']
        dt_now = datetime.now()
        num_of_days_in_month = calendar.monthrange(dt_now.year, dt_now.month)[1]
        # request_id = request_obj.search([
        #     ('state', 'not in', ('validated', 'cancelled')),
        #     ('create_date', '>=', dt_now + relativedelta(day=1, hour=0, minute=0, second=0)),
        #     ('create_date', '<=', dt_now + relativedelta(day=num_of_days_in_month, hour=23, minute=59, second=59)),
        # ])
        # if not request_id:
        #     request_id = request_obj.create({'name': 'Request for ' + dt_now.strftime("%B, %Y")})

        # request_line_id = request_line_obj.search([('work_entry_id', '=', self.id)])
        # if not request_line_id:
        vals=[]
        for line in self:
            request_line_record=line.adjustment_request_ids.filtered(lambda x: x.state == "draft")
            if line.state in ['draft','validated','conflict','cancelled']:
                continue

            elif line.state =='confirmed':
                vals.append({
                    'wizard_id': wz_id.id,
                    'employee_id': line.employee_id.id,
                    'work_entry_id': line.id,
                    'old_date_start': line.actual_start,
                    'old_date_stop': line.actual_stop,
                    'old_duration': line.actual_duration,
                    'new_date_start': line.actual_start,
                    'new_date_stop': line.actual_stop,
                    'break_time':line.break_time,
                })
                if request_line_record:
                    vals[0].update({
                        'new_date_start': request_line_record.new_date_start,
                        'new_date_stop': request_line_record.new_date_stop,
                        })
        request_line = request_line_obj.create(vals)
        return {
            'name': _('Make A Timesheet Adjustment Request'),
            'view_mode': 'form',
            'view_id': self.env.ref('erpvn_hr_work_entry.wizards_adjustment_request_line_form_view').id,
            'res_model': 'wizard.timesheet.adjustment.request',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': wz_id.id,
        }

    def _get_utc_tz(self, attendence_id, current_date):
        base_obj = self.env['erpvn.base']

        user_tz_dt_start = datetime.combine(current_date, float_to_time(attendence_id.hour_from))
        user_tz_dt_stop = datetime.combine(current_date, float_to_time(attendence_id.hour_to))
        if attendence_id.dayofweek != attendence_id.dayofweek_to:
            day_fr = int(attendence_id.dayofweek)
            day_to = int(attendence_id.dayofweek_to)
            if day_to < day_fr:
                day_fr -= 7
            user_tz_dt_stop = datetime.combine(current_date + timedelta(days=day_to-day_fr), float_to_time(attendence_id.hour_to))

        utc_tz_dt_start = base_obj.convert_time_to_utc(dt=user_tz_dt_start).replace(tzinfo=None)
        utc_tz_dt_stop = base_obj.convert_time_to_utc(dt=user_tz_dt_stop).replace(tzinfo=None)

        return utc_tz_dt_start, utc_tz_dt_stop

    def _prepare_work_entry_vals(self, contract_id, attendence_id, current_date, utc_tz_dt_start, utc_tz_dt_stop):
        breaking_hours = 0.0

        base_obj = self.env['erpvn.base']
        tz = attendence_id.calendar_id.tz

        start_time_tz = base_obj.convert_utc_time_to_tz(utc_tz_dt_start, tz).time()
        start_float = start_time_tz.hour + start_time_tz.minute/60.0

        stop_time_tz = base_obj.convert_utc_time_to_tz(utc_tz_dt_stop, tz).time()
        stop_float = stop_time_tz.hour + stop_time_tz.minute/60.0

        for break_id in attendence_id.break_time_ids:
            break_duration = self._get_breaking_hours(break_id, start_float, stop_float)
            if break_duration > 0.0:
                breaking_hours += break_duration

        results = {
            'name': current_date.date().strftime("%a") + ', ' + current_date.strftime("%Y-%m-%d"),
            'employee_id': contract_id.employee_id.id,
            'attendance_id': attendence_id.id,
            'resource_calendar_id': attendence_id.calendar_id.id,
            'work_entry_type_id': attendence_id.work_entry_type_id.id,
            'date_start': utc_tz_dt_start,
            'date_stop': utc_tz_dt_stop,
            'break_time': breaking_hours,
            'tz': tz,
            'contract_id': contract_id.id,
        }
        if attendence_id.no_fingerprint_required or contract_id.no_required_attendance:
            results.update({
                'state': 'validated',
                'actual_start': utc_tz_dt_start,
                'actual_stop': utc_tz_dt_stop,
            })        

        return results

    @api.model
    def _create_hr_work_entry(self):
        work_entry_obj = self.env['hr.work.entry']

        work_entry_vals = []

        # FOR PRODUCT.
        first_date_of_next_month = self.sudo().env.ref('erpvn_hr_work_entry.ir_cron_create_hr_work_entry').nextcall + relativedelta(day=1, hour=0, minute=0, second=0)

        # not_used: is weekday of first day of the month
        not_used, number_of_days_in_month = calendar.monthrange(first_date_of_next_month.year, first_date_of_next_month.month)
        user_tz_last_date_of_next_month = first_date_of_next_month + timedelta(days=number_of_days_in_month-1) + relativedelta(hour=23, minute=59, second=59)

        date_temp = first_date_of_next_month + relativedelta(months=1)
        date_start_next_month = date_temp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        contract_ids = self.env['hr.contract'].search([
            ('state', 'in', ('open', 'close', 'expiring')),
            '|', ('date_end', '=', False), ('date_end', '>=', date_start_next_month)
        ])
        for contract_id in contract_ids:
            # current_date: datetime.date(2021, 10, 1) -> datetime.date(2021, 10, 31)
            current_date = first_date_of_next_month
            # days_of_week = ['0', '1', '2', '3', '4', '5', '6']
            days_of_week = list(set(contract_id.resource_calendar_id.attendance_ids.mapped('dayofweek')))
            while current_date <= user_tz_last_date_of_next_month:
                # contract_id.date_end: datetime.date(2021, 10, 16)
                # -> i = datetime.date(2021, 10, 17) --> break and go to next contract.
                if contract_id.date_end:
                    if contract_id.date_end < current_date.date():
                        break
                if str(current_date.weekday()) in days_of_week:
                    for attendence_id in contract_id.resource_calendar_id.attendance_ids.filtered(lambda x: x.dayofweek == str(current_date.weekday())):
                        utc_tz_dt_start, utc_tz_dt_stop = self._get_utc_tz(attendence_id, current_date)

                        if contract_id.employee_id.work_entry_ids.filtered_domain([
                            ('attendance_id', '=', attendence_id.id),
                            ('date_start', '=', utc_tz_dt_start),
                            ('date_stop', '=', utc_tz_dt_stop)
                        ]): # check if existed work entry.
                            continue

                        # check if there is a intersection datetimerange for new work entry.
                        if contract_id.employee_id.work_entry_ids.filtered(lambda x: x.date_start and x.date_stop)\
                            .filtered(lambda y: y.date_start <= utc_tz_dt_stop and y.date_stop >= utc_tz_dt_start):
                            continue

                        # check if there is a public holidays.
                        if self.env['hr.leave'].sudo().search_count([
                            ('state', '=', 'validate'),
                            ('date_from', '<=', utc_tz_dt_start),
                            ('date_to', '>=', utc_tz_dt_stop),
                            ('employee_id', '=', contract_id.employee_id.id),
                            ('holiday_status_id.code', 'in', HOLIDAY_CODES)]) > 0:
                            continue

                        val = self._prepare_work_entry_vals(contract_id, attendence_id, current_date, utc_tz_dt_start, utc_tz_dt_stop)

                        if self.env['hr.leave'].sudo().search_count([
                            ('state', '=', 'validate'),
                            ('date_from', '<=', utc_tz_dt_start),
                            ('date_to', '>=', utc_tz_dt_stop),
                            ('employee_id', '=', contract_id.employee_id.id)]) > 0:
                            val.update({
                                'state': 'validated',
                                'actual_start': utc_tz_dt_start,
                                'actual_stop': utc_tz_dt_stop,
                            })

                        if val not in work_entry_vals:
                            work_entry_vals.append(val)
                            
                current_date += timedelta(days=1)
            
        if work_entry_vals:
            work_entry_obj.create(work_entry_vals)

    def get_format_timezone_start(self):
        self.ensure_one()
        if self.date_start:
            base_obj = self.env['erpvn.base']
            start_entry_tz = base_obj.convert_utc_time_to_tz(self.date_start, self.tz).replace(tzinfo=None)
            return start_entry_tz.strftime("%d/%m/%Y, %H:%M:%S")
        return ''

    # get string date_stop format for mail.template
    def get_format_timezone_stop(self):
        self.ensure_one()
        if self.date_stop:
            base_obj = self.env['erpvn.base']
            stop_entry_tz = base_obj.convert_utc_time_to_tz(self.date_stop, self.tz).replace(tzinfo=None)
            return stop_entry_tz.strftime("%d/%m/%Y, %H:%M:%S")
        return ''

    @api.model
    def _notify_invalid_attendances(self):
        base_obj = self.env['erpvn.base']
        leave_obj = self.env['hr.leave']
        work_entry_obj = self.env['hr.work.entry']

        utc_tz_date = self.sudo().env.ref('erpvn_hr_work_entry.ir_cron_notify_invalid_attendances').nextcall

        # the cron run at 05/21/2022 => the_previous_dt_range: 05/21/2022 00:00:00 - 05/21/2022 23:59:59
        the_previous_dt_range = DateTimeRange(utc_tz_date + relativedelta(days=-1, hours=0, minutes=0, seconds=0), utc_tz_date + relativedelta(days=-1, hour=23, minute=59, second=59))
        
        # check for work entries that has state = draft and is in period the_previous_dt_range to confirm.
        wort_entries_to_confirm=work_entry_obj.search([('date_start','>=',the_previous_dt_range.start_datetime),('date_stop','<=',the_previous_dt_range.end_datetime),('state','=','draft')])
        wort_entries_to_confirm.action_confirm_multi()

        record_with_date_start_stop_no_valid_attendances = work_entry_obj.search([
            ('state', '=', 'confirmed'),
            ('actual_duration', '=', 0.0),
            ('duration', '!=', 0.0), # make sure record have start and stop fields.
        ])
        # prevent error in case work.entry without date_start/date_stop => error if compare to DateTimeRange.
        invalid_records = record_with_date_start_stop_no_valid_attendances.filtered(lambda x: x.date_start in the_previous_dt_range and x.date_stop in the_previous_dt_range)

        # check if there is a approved leave on the work entry.
        holidays = leave_obj.search([('state', '=', 'validate'), ('employee_id', 'in', invalid_records.employee_id.ids)])

        # compare leave and work entry, and get final invalid work entry.
        invalid_without_leaves = work_entry_obj
        for entry in invalid_records:
            if (entry.employee_id.id not in holidays.employee_id.ids) or \
                (not holidays.filtered(lambda x: x.employee_id.id == entry.employee_id.id and entry.date_start >= x.date_from and entry.date_stop <= x.date_to)): # compare datetime_range between work entry and approved leave.
                invalid_without_leaves |= entry

        employee_manager_ids = invalid_without_leaves.employee_id.parent_id
        dict_val = defaultdict(lambda: work_entry_obj)
        for manager in employee_manager_ids:
            dict_val[manager] = invalid_without_leaves.filtered(lambda x: x.employee_id.parent_id.id == manager.id)
        
        template_id = self.env.ref('erpvn_hr_work_entry.notify_invalid_attendance_mail_template')

        if dict_val:
            for manager, entries in dict_val.items():
                ctx = defaultdict(list)
                ctx['data'] = entries
                
                # get manager user.
                manager_user = base_obj.get_parent_employee_user(manager)

                if manager_user:
                    base_obj.send_mail_template(self, template_id, manager_user, ctx)

    @api.model
    def _confirm_workentries_automatically(self):
        work_entry_obj = self.env['hr.work.entry']
        date_to_confirm = self.sudo().env.ref('erpvn_hr_work_entry.ir_cron_confirm_work_entry').nextcall.date()
        
        for w in work_entry_obj.search([
            ('date_start', '>=', datetime.combine(date_to_confirm, datetime.min.time())), 
            ('date_start', '<', datetime.combine(date_to_confirm, datetime.max.time())),
            ('state', '=', 'draft'),
        ]):
            w.action_confirm()

    def unlink(self):
        if not self.env.user.has_group('base.group_system'):
            raise UserError(_('You cannot delete the work entry.'))
        return super(HrWorkEntry, self).unlink()
    
    @api.onchange('resource_calendar_id')
    def _update_working_shift(self):
        for rec in self:
            rec.write({
                'is_flexible_time': rec.resource_calendar_id.is_flexible_time,
                'flex_hour_from': rec.resource_calendar_id.flex_hour_from,
                'flex_hour_to': rec.resource_calendar_id.flex_hour_to,
                'flex_hour_out': rec.resource_calendar_id.flex_hour_out,
                'flex_hour_limit_out': rec.resource_calendar_id.flex_hour_limit_out,
            })
    
    def _update_flexible_time(self):
        self.ensure_one()
        self.write({
            'is_flexible_time': self.resource_calendar_id.is_flexible_time,
            'flex_hour_from': self.resource_calendar_id.flex_hour_from,
            'flex_hour_to': self.resource_calendar_id.flex_hour_to,
            'flex_hour_out': self.resource_calendar_id.flex_hour_out,
            'flex_hour_limit_out': self.resource_calendar_id.flex_hour_limit_out,
        })

    def update_flexible_time(self):
        for rec in self.filtered(lambda x: x.resource_calendar_id.is_flexible_time):
            rec._update_flexible_time()


class WizardTimesheetLine(models.TransientModel):
    _name = 'wizard.timesheet.line'
    _order = 'sequence'
    _description = "Wizard Timesheet Line"

    sequence = fields.Integer(default=1, index=True)
    name = fields.Char('Name')
    overtime_id = fields.Many2one('hr.work.entry', 'Working Shift', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    barcode = fields.Char(related='employee_id.barcode', string='Barcode')
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id")
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id", store=True)
    # manager_id = fields.Many2one('res.users', string='Manager')
    # duration = fields.Float(string='Duration', store=True, compute='_compute_duration')
    # break_time = fields.Float(string='Break Time', store=True, compute='_compute_duration')
    # attendance_ids = fields.One2many(string='Attendances', comodel_name='hr.attendance')
    # actual_time = fields.Float(string='Actual Time', compute='_compute_time_actual', store=True)
    # work_entry_ids = fields.One2many('hr.work.entry', 'overtime_line_id', string='Work Entries', tracking=True)
    status = fields.Selection([
            ('has-overtime', 'Duplicated Overtime'),
            ('valid', 'Valid'),
            ('has-shift', 'Existed Shift'),
            ('cancel', 'Cancelled')
        ], string="Status", default="valid")
    # state = fields.Selection(related='overtime_id.state', string='Overtime State', readonly=True, copy=False, store=True, default='draft')
    note = fields.Text('Note')

    overtime_day = fields.Date(string='Date', required=True)
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
        ('23', '23:00'), ('23.25', '23:15'), ('23.5', '23:30'), ('23.75', '23:45')], string='Hour From', required=True)

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
        ('23', '23:00'), ('23.25', '23:15'), ('23.5', '23:30'), ('23.75', '23:45')], string='Hour To', required=True)