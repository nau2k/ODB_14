# -*- coding: utf-8 -*-
import pytz
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from datetimerange import DateTimeRange

class HrOvertimeLine(models.Model):
    _name = 'hr.overtime.line'
    _order = 'id desc'
    _description = "HR Overtime Line"
    _inherit = 'mail.thread'

    @api.depends('attendance_ids')
    def _compute_time_actual(self):
        self.actual_time = sum(self.attendance_ids.mapped('worked_hours'))

    def _get_attendance(self):
        for line in self:
            check_in = datetime.strptime(str(line.overtime_day) + " " + str(timedelta(hours = float(line.hour_from))), '%Y-%m-%d %H:%M:%S')
            check_out = datetime.strptime(str(line.overtime_day) + " " + str(timedelta(hours = float(line.hour_to))), '%Y-%m-%d %H:%M:%S')
            self.attendance_ids = self.env['hr.attendance'].search([
                ('employee_id', '=', line.employee_id.id),
                ('check_in', '>=', check_in),
                ('check_out', '<=', check_out),
            ])

    sequence = fields.Integer(default=1, index=True)
    name = fields.Char('Name')
    overtime_id = fields.Many2one('hr.overtime', 'Overtime', ondelete='cascade', index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    employee_code = fields.Char(related='employee_id.barcode', string='Barcode',store=True)
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id", store=True)
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id", store=True)
    manager_id = fields.Many2one('res.users', string='Manager')
    duration = fields.Float(string='Duration', store=True, compute='_compute_duration')
    break_time = fields.Float(string='Break Time', store=True, compute='_compute_duration')
    attendance_ids = fields.One2many(string='Attendances', comodel_name='hr.attendance', compute=_get_attendance)
    actual_time = fields.Float(string='Actual Time', compute='_compute_time_actual', store=True)
    work_entry_ids = fields.One2many('hr.work.entry', 'overtime_line_id', string='Work Entries', tracking=True)
    status = fields.Selection([
            ('has-overtime', 'Duplicated Overtime'),
            ('valid', 'Valid'),
            ('has-shift', 'Existed Shift'),
            ('cancel', 'Cancelled')
        ], string="Status", default="valid")
    state = fields.Selection(related='overtime_id.state', string='Overtime State', readonly=True, copy=False, store=True, default='draft')
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

    def name_get(self):
        result = []
        for line in self:
            name = '[' + str(line.employee_code) + '] ' + line.employee_id.name
            result.append((line.id, name))
        return result

    @api.depends('hour_from', 'hour_to')
    def _compute_duration(self):
        for record in self:
            period = 0.0
            if record.hour_from and record.hour_to:
                
                overtime_id = record.overtime_id

                from_datetime = datetime.combine(record.overtime_day, datetime.min.time()) + timedelta(hours=float(record.hour_from))
                to_datetime = datetime.combine(record.overtime_day, datetime.min.time()) + timedelta(hours=float(record.hour_to))

                period = float(record.hour_to) - float(record.hour_from)
                if float(record.hour_to) < float(record.hour_from):
                    period = 24.0 - float(record.hour_from) + float(record.hour_to)
                    to_datetime = datetime.combine(record.overtime_day, datetime.min.time()) + timedelta(days=1, hours=float(record.hour_to))
                
                local_tz = pytz.timezone(overtime_id.resource_calendar_id.tz)
                from_datetime = local_tz.localize(from_datetime)
                to_datetime = local_tz.localize(to_datetime)

                intervals = overtime_id.resource_calendar_id._attendance_intervals_batch(from_datetime, to_datetime, overtime_id.resource_calendar_id)

                break_time = 0.0
                for start, stop, meta in intervals[overtime_id.resource_calendar_id.id]:
                    break_duration = overtime_id.resource_calendar_id._get_breaking_hours(meta, start, stop)
                    if break_duration > 0.0:
                        break_time += break_duration

                if break_time > 0.0:
                    period -= break_time

                record.break_time = break_time

            record.duration = period
    
    def get_day(self):
        self.ensure_one()
        if self.hour_from:
            dt_fom = datetime.combine(self.overtime_day, datetime.min.time()) + timedelta(hours=float(self.hour_from))
            return dt_fom.strftime("%d/%m/%Y")
        return ''

    def get_datetime_from(self):
        self.ensure_one()
        if self.hour_from:
            dt_fom = datetime.combine(self.overtime_day, datetime.min.time()) + timedelta(hours=float(self.hour_from))
            return dt_fom.strftime("%H:%M")
        return ''

    def get_datetime_to(self):
        self.ensure_one()
        if self.hour_to:
            dt_to = datetime.combine(self.overtime_day, datetime.min.time()) + timedelta(hours=float(self.hour_to))
            return dt_to.strftime("%H:%M")
        return ''

    def get_duration(self):
        self.ensure_one()
        if self.duration:
            hours,minutes=divmod(self.duration * 60, 60)
            return "{:02.0f}:{:02.0f}".format(hours, minutes)
        return '00:00'

    def get_break_time(self):
        self.ensure_one()
        if self.break_time:
            hours,minutes=divmod(self.break_time * 60, 60)
            return "{:02.0f}:{:02.0f}".format(hours, minutes)
        return '00:00'
    

    @api.onchange('employee_id', 'overtime_day', 'hour_from', 'hour_to')
    def _check_line_status(self):
        for line in self:
            if not (line.employee_id and line.overtime_day and line.hour_from and line.hour_to):
                continue

            line.status = line._check_status()

    def _check_status(self):
        self.ensure_one()
        self = self.sudo()
        base_obj = self.env['erpvn.base']

        employee_id = self.employee_id
        overtime_id = self.overtime_id
        ot_date = self.overtime_day
        tz = overtime_id.tz
        status = 'valid'


        hour_from = float(self.hour_from)
        hour_to = float(self.hour_to)

        from_datetime = datetime.combine(ot_date, datetime.min.time()) + timedelta(hours=hour_from)
        to_datetime = datetime.combine(ot_date, datetime.min.time()) + timedelta(hours=hour_to)

        duration = hour_to - hour_from
        break_time = 0.0

        if hour_to < hour_from:
            duration = 24.0 - hour_from + hour_to
            to_datetime = datetime.combine(ot_date, datetime.min.time()) + timedelta(days=1, hours=hour_to)
        
        local_tz = pytz.timezone(overtime_id.resource_calendar_id.tz)
        from_datetime = local_tz.localize(from_datetime)
        to_datetime = local_tz.localize(to_datetime)

        intervals = overtime_id.resource_calendar_id._attendance_intervals_batch(from_datetime, to_datetime, overtime_id.resource_calendar_id)

        for start, stop, meta in intervals[overtime_id.resource_calendar_id.id]:
            break_duration = overtime_id.resource_calendar_id._get_breaking_hours(meta, start, stop)
            if break_duration > 0.0:
                break_time += break_duration

        if break_time > 0.0:
            duration -= break_time

        datetime_from = datetime.combine(ot_date, datetime.min.time()) + timedelta(hours=hour_from)
        datetime_to = datetime_from + timedelta(hours=(duration + break_time))

        # get status depends on existed hr.overtime.line or hr.work.entry

        # convert to UTC timezone to save to database.
        time_range = DateTimeRange(
            base_obj.convert_time_to_utc(datetime_from, tz_name=tz).replace(tzinfo=None),
            base_obj.convert_time_to_utc(datetime_to, tz_name=tz).replace(tzinfo=None)
        )

        employee_ot_lines = employee_id.overtime_line_ids.filtered(lambda x: x.overtime_id.state != 'cancelled' \
                            and x.status == 'valid' and x.overtime_day == ot_date and x.hour_from and x.hour_to)

        if self._origin:
            employee_ot_lines -= self._origin

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
            if employee_id.work_entry_ids.filtered(lambda x: x.state != 'cancelled' and x.date_start and x.date_stop)\
                .filtered(lambda y: time_range.is_intersection(DateTimeRange(y.date_start, y.date_stop)) and \
                    not (time_range.start_datetime == y.date_stop) and not (y.date_start == time_range.end_datetime)):
                status = 'has-shift'
        
        return status