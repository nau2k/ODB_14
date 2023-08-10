# -*- coding: utf-8 -*-
import math
from collections import defaultdict, namedtuple
from pytz import timezone, utc
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, DAILY, WEEKLY
from odoo.addons.resource.models.resource import float_to_time, Intervals
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import float_utils

ROUNDING_FACTOR = 16

class Calendar(models.Model):
    _name = 'resource.calendar'
    _inherit = ['resource.calendar', 'mail.thread']
    _order = 'sequence, id'
    _interval_obj = namedtuple('Interval', ('start_datetime', 'end_datetime', 'data'))

    # odoo's fields.
    name = fields.Char(tracking=True)
    active = fields.Boolean(tracking=True)
    company_id = fields.Many2one(tracking=True)
    hours_per_day = fields.Float(tracking=True)
    tz = fields.Selection(tracking=True)
    two_weeks_calendar = fields.Boolean(tracking=True)
    two_weeks_explanation = fields.Char(tracking=True)

    # customized fields.
    hours_per_week = fields.Float(tracking=True)
    full_time_required_hours = fields.Float(tracking=True)
    is_fulltime = fields.Boolean(tracking=True)
    work_time_rate = fields.Float(tracking=True)

    sequence = fields.Integer(string="Sequence", required=True, default=10, help="Sequence", tracking=True)
    color = fields.Integer(string='Color Index', help="Color", tracking=True)
    note = fields.Text(string='Note')

    # flexible time
    is_flexible_time = fields.Boolean(string="Flexible Time", tracking=True)
    flex_hour_from = fields.Float(string='Flexible From', tracking=True)
    flex_hour_to = fields.Float(string='Flexible To', tracking=True)
    flex_hour_out = fields.Float(string='Flexible Out', tracking=True)
    flex_hour_limit_out = fields.Float(string='Flexible Limit Out', tracking=True)

    def _get_breaking_hours(self, attendance, start, stop, calendar=None):
        if calendar:
            start_calendar_tz = start.tzinfo.localize(start.replace(tzinfo=None)).astimezone(timezone(calendar.tz))
            return sum(calendar.attendance_ids.filtered(lambda x: x.dayofweek == str(start_calendar_tz.date().weekday())).break_time_ids.mapped('duration'))

        result = 0.0

        ac_start_float = start.time().hour + start.time().minute/60.0
        ac_stop_float = stop.time().hour + stop.time().minute/60.0

        for break_id in attendance.break_time_ids:
            break_duration = 0.0
            
            if ac_start_float <= break_id.hour_from and ac_stop_float >= break_id.hour_to:
                break_duration = break_id.duration
            elif ac_start_float > break_id.hour_from and ac_stop_float >= break_id.hour_to:
                break_duration = break_id.hour_to - ac_start_float
            elif ac_start_float <= break_id.hour_from and ac_stop_float < break_id.hour_to:
                break_duration = ac_stop_float - break_id.hour_from

            if break_duration > 0.0:
                result += break_duration

        return result

    def _check_overlap(self, attendance_ids):
        if not attendance_ids.filtered(lambda att: not att.date_from and not att.date_to).filtered(lambda x: x.dayofweek != x.dayofweek_to):
            super(Calendar, self)._check_overlap(attendance_ids)
        else:
            result = []
            for attendance in attendance_ids.filtered(lambda att: not att.date_from and not att.date_to):
                day_fr = int(attendance.dayofweek)
                day_to = int(attendance.dayofweek_to)
                if attendance.dayofweek != attendance.dayofweek_to:
                    days = day_to - day_fr
                    if day_to < day_fr:
                        days = day_to - (day_fr - 7)
                    for i in range(days + 1):
                        hour_fr = 0.0
                        hour_to = 23.99
                        if day_fr == int(attendance.dayofweek):
                            hour_fr = attendance.hour_from
                        elif day_fr == int(attendance.dayofweek_to):
                            hour_to = attendance.hour_to
                        result.append((day_fr * 24 + hour_fr + 0.000001, day_fr * 24 + hour_to, attendance))
                        if day_fr == 6:
                            day_fr = 0
                        else:
                            day_fr += 1
                else:
                    result.append((day_fr * 24 + attendance.hour_from + 0.000001, day_fr * 24 + attendance.hour_to, attendance))

            if len(Intervals(result)) != len(result):
                raise ValidationError(_("Attendances can't overlap."))

    def _compute_hours_per_day(self, attendances):
        # no overday, no break time => call default func.
        if not attendances.filtered(lambda x: x.dayofweek != x.dayofweek_to or x.break_time_ids):
            return super(Calendar, self)._compute_hours_per_day(attendances)

        # customized func.s
        if not attendances:
            return 0
        hour_count = sum(attendances.mapped('estimated_hours')) + sum(attendances.break_time_ids.mapped('duration'))
        if self.two_weeks_calendar:
            number_of_days = len(set(attendances.filtered(lambda cal: cal.week_type == '1').mapped('dayofweek')))
            number_of_days += len(set(attendances.filtered(lambda cal: cal.week_type == '0').mapped('dayofweek')))
        else:
            number_of_days = len(set(attendances.mapped('dayofweek')))
        return float_round(hour_count / float(number_of_days), precision_digits=2)

    @api.depends('attendance_ids')
    def _compute_hours_per_week(self):
        if not self.attendance_ids.filtered(lambda x: x.dayofweek != x.dayofweek_to or x.break_time_ids):
            super(Calendar, self)._compute_hours_per_week()
        else:
            for calendar in self:
                sum_hours = sum(calendar.attendance_ids.mapped('estimated_hours')) + sum(x.break_time_ids.duration for x in calendar.attendance_ids)
                calendar.hours_per_week = sum_hours / 2 if calendar.two_weeks_calendar else sum_hours

    # override default method. cause, default it does not count with resource.calendar.attendance with over_days > 0.
    def _attendance_intervals_batch(self, start_dt, end_dt, resources=None, domain=None, tz=None):
        self.ensure_one()
        resources = self.env['resource.resource'] if not resources else resources
        assert start_dt.tzinfo and end_dt.tzinfo
        self.ensure_one()
        
        resources_list = list(resources) + [self.env['resource.resource']]
        resource_ids = [r.id for r in resources_list]
        domain = domain if domain is not None else []
        domain = expression.AND([domain, [
            ('calendar_id', '=', self.id),
            ('resource_id', 'in', resource_ids),
            ('display_type', '=', False),
        ]])

        # call to odoo's func in case there is no attendance with overdays range.
        if not self.env['resource.calendar.attendance'].search(domain).filtered(lambda x: x.dayofweek != x.dayofweek_to):
            return super(Calendar, self)._attendance_intervals_batch(start_dt, end_dt, resources, domain, tz)

        combine = datetime.combine
        # for each attendance spec, generate the intervals in the date range
        cache_dates = defaultdict(dict)
        cache_deltas = defaultdict(dict)
        result = defaultdict(list)
        for attendance in self.env['resource.calendar.attendance'].search(domain):
            weekday = int(attendance.dayofweek)
            over_days = 0
            if attendance.dayofweek != attendance.dayofweek_to:
                day_fr = int(attendance.dayofweek)
                day_to = int(attendance.dayofweek_to)
                while day_fr != day_to:
                    over_days += 1
                    day_fr += 1
                    if day_fr > 6:
                        day_fr = 0
            i = 0
            while i <= over_days:
                for resource in resources_list:
                    # express all dates and times in specified tz or in the resource's timezone
                    tz = tz if tz else timezone((resource or self).tz)
                    if (tz, start_dt) in cache_dates:
                        start = cache_dates[(tz, start_dt)]
                    else:
                        start = start_dt.astimezone(tz)
                        cache_dates[(tz, start_dt)] = start
                    if (tz, end_dt) in cache_dates:
                        end = cache_dates[(tz, end_dt)]
                    else:
                        end = end_dt.astimezone(tz)
                        cache_dates[(tz, end_dt)] = end

                    start = start.date()
                    if attendance.date_from:
                        att_date_from = attendance.date_from
                        if i > 0:
                            att_date_from = attendance.date_from + relativedelta(days=i)
                        start = max(start, att_date_from)

                    until = end.date()
                    if attendance.date_to:
                        att_date_to = attendance.date_from
                        if i > 0:
                            att_date_to = attendance.date_from + relativedelta(days=i)
                        until = min(until, att_date_to)
                        
                    if attendance.week_type:
                        start_week_type = int(math.floor((start.toordinal()-1)/7) % 2)
                        if start_week_type != int(attendance.week_type):
                            start = start + relativedelta(weeks=-1)

                    if i > 0:
                        if weekday == 6:
                            weekday = 0
                        else:
                            weekday += 1
                        # weekday += 1
                        # if weekday == 7:
                        #     weekday = 0

                    if self.two_weeks_calendar and attendance.week_type:
                        days = rrule(WEEKLY, start, interval=2, until=until, byweekday=weekday)
                    else:
                        days = rrule(DAILY, start, until=until, byweekday=weekday)

                    for day in days:
                        # attendance hours are interpreted in the resource's timezone
                        hour_from = attendance.hour_from
                        if i > 0:
                            hour_from = 0.0
                        if (tz, day, hour_from) in cache_deltas:
                            dt0 = cache_deltas[(tz, day, hour_from)]
                        else:
                            dt0 = tz.localize(combine(day, float_to_time(hour_from)))
                            cache_deltas[(tz, day, hour_from)] = dt0

                        hour_to = 24.0
                        if i == over_days:
                            hour_to = attendance.hour_to
                        if (tz, day, hour_to) in cache_deltas:
                            dt1 = cache_deltas[(tz, day, hour_to)]
                        else:
                            dt1 = tz.localize(combine(day, float_to_time(hour_to)))
                            cache_deltas[(tz, day, hour_to)] = dt1
                        result[resource.id].append((max(cache_dates[(tz, start_dt)], dt0), min(cache_dates[(tz, end_dt)], dt1), attendance))
                i += 1
        return {r.id: Intervals(result[r.id]) for r in resources_list}

    # overload odoo's func to subtract breaking hours.
    def _get_days_data(self, intervals, day_total):
        if filter(lambda x: x[2].break_time_ids, intervals):
            day_hours = defaultdict(float)
            for start, stop, meta in intervals:
                day_hours[start.date()] += ((stop - start).total_seconds() / 3600) - self._get_breaking_hours(meta, start, stop)

            # compute number of days as quarters
            days = sum(
                day_hours[day] / day_total[day] if day_total[day] else 0
                for day in day_hours
            )
            return {'days': days, 'hours': sum(day_hours.values())}
        return super(Calendar, self)._get_days_data(intervals, day_total)

    # overide odoo's func to subtract breaking hours.
    def get_work_hours_count(self, start_dt, end_dt, compute_leaves=True, domain=None):
        self.ensure_one()
        result = super(Calendar, self).get_work_hours_count(start_dt, end_dt, compute_leaves=True, domain=None)
        
        # Set timezone in UTC if no timezone is explicitly given
        if not start_dt.tzinfo:
            start_dt = start_dt.replace(tzinfo=utc)
        if not end_dt.tzinfo:
            end_dt = end_dt.replace(tzinfo=utc)

        if compute_leaves:
            intervals = self._work_intervals_batch(start_dt, end_dt, domain=domain)[False]
        else:
            intervals = self._attendance_intervals_batch(start_dt, end_dt)[False]
        return result - sum(self._get_breaking_hours(meta, start, stop) for start, stop, meta in intervals)

    def _get_resources_day_total(self, from_datetime, to_datetime, resources=None):
        self.ensure_one()
        result = super(Calendar, self)._get_resources_day_total(from_datetime, to_datetime, resources=None)

        resources = self.env['resource.resource'] if not resources else resources
        resources_list = list(resources) + [self.env['resource.resource']]
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = self._attendance_intervals_batch(from_full, to_full, resources=resources)

        for resource in resources_list:
            day_total = result[resource.id]
            for start, stop, meta in intervals[resource.id]:
                day_total[start.date()] += (stop - start).total_seconds() / 3600
                if meta.break_time_ids:
                    breaking_hours = self._get_breaking_hours(meta, start, stop)
                    if day_total[start.date()] > 0.0 and day_total[start.date()] > breaking_hours:
                        day_total[start.date()] -= breaking_hours
        return result