# -*- coding: utf-8 -*-
import logging
from datetime import timedelta, datetime as dt, time
from dateutil.relativedelta import relativedelta
from datetimerange import DateTimeRange
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from ...erpvn_base.models.base import OdooBase

_logger = logging.getLogger(__name__)


class AttendanceWizard(models.TransientModel):
    _name = 'attendance.wizard'
    _description = 'Attendance Wizard'

    @api.model
    def _get_all_device_ids(self):
        return self.env['attendance.device'].search([('state', '=', 'confirmed')]).ids

    device_ids = fields.Many2many('attendance.device', string='Devices',
        default=_get_all_device_ids, domain=[('state', '=', 'confirmed')])
    fix_attendance_valid_before_synch = fields.Boolean(string='Fix Attendance Valid', help="If checked, Odoo will recompute all attendance data for their valid"
        " before synchronizing with HR Attendance (upon you hit the 'Synchronize Attendance' button)")
    date_from = fields.Date(string='Date From', default=fields.Date.today() - timedelta(days=3), required=True,)
    date_to = fields.Date(string='Date To', default=fields.Date.today(), required=True,)
    department_id = fields.Many2one(string='Department', comodel_name='hr.department')
    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee')
    
    def action_download_attendance(self):
        if not self.device_ids:
            raise UserError(_('You must select at least one device to continue!'))
        range_date = DateTimeRange(dt.combine(self.date_from, time.min), dt.combine(self.date_to, time.max))
        self.device_ids.action_attendance_download(range_date, self.department_id, self.employee_id)

    def cron_download_device_attendance(self):
        devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        dt_from = OdooBase.convert_utc_time_to_tz(self,fields.Datetime.now()).replace(tzinfo=None) - timedelta(hours=self.env.company.limited_hours_to_get_attendances)
        dt_to = OdooBase.convert_utc_time_to_tz(self,fields.Datetime.now()).replace(tzinfo=None)
        range_date = DateTimeRange(dt_from,dt_to)
        devices.action_attendance_download(range_date)

    # manh.nv on July 6, 2023: un-use func.
    # def cron_user_attendance_validate(self, date_from=None, date_to=None):
    #     if not date_from and not date_to:
    #         date_from =  dt.combine(dt.today() + relativedelta(day=1), time.min)
    #         date_to = dt.combine(fields.Datetime.now(), time.max)
    #     user_attendance = self.env['user.attendance'].search([('timestamp', '>=', date_from), ('timestamp', '>=', date_to)])
    #     for att in user_attendance:
    #         att.action_attendace_validated()

    def cron_sync_attendance(self):
        # Manh: not used.
        # range_date = DateTimeRange(fields.Date.today() - timedelta(days=1), str(fields.Date.today())+' 23:59:59')
        self.with_context(synch_ignore_constraints=True).sync_attendance()

    def sync_attendance(self):
        """
        This method will synchronize all downloaded attendance data with Odoo attendance data.
        It do not download attendance data from the devices.
        """
        if self.fix_attendance_valid_before_synch:
            self.action_fix_user_attendance_valid()

        synch_ignore_constraints = self.env.context.get(
            'synch_ignore_constraints', False)

        error_msg = {}
        HrAttendance = self.env['hr.attendance'].with_context(
            synch_ignore_constraints=synch_ignore_constraints)

        work_entry_type_ids = self.env['hr.work.entry.type'].search([])

        DeviceUserAttendance = self.env['user.attendance']

        last_employee_attendance = {}

        dt_now = fields.Datetime.now()
        limited_dt = dt_now - timedelta(hours=self.env.company.limited_hours_to_get_attendances)

        for work_entry_type_id in work_entry_type_ids:
            if work_entry_type_id.id not in last_employee_attendance.keys():
                last_employee_attendance[work_entry_type_id.id] = {}

            unsync_data = DeviceUserAttendance.search([('hr_attendance_id', '=', False),
                ('valid', '=', True),
                ('employee_id', '!=', False),
                ('work_entry_type_id', '=', work_entry_type_id.id)], order='timestamp ASC')
            for att in unsync_data:
                if att.timestamp < limited_dt or att.timestamp > dt_now:
                    continue

                employee_id = att.user_id.employee_id
                if employee_id.id not in last_employee_attendance[work_entry_type_id.id].keys():
                    last_employee_attendance[work_entry_type_id.id][employee_id.id] = False

                if att.type == 'check_out':
                    # find last attendance
                    last_employee_attendance[work_entry_type_id.id][employee_id.id] = HrAttendance.search(
                        [('employee_id', '=', employee_id.id),
                         ('work_entry_type_id', 'in', (work_entry_type_id.id, False)),
                         ('check_in', '<=', att.timestamp)], limit=1, order='check_in DESC')

                    hr_attendance_id = last_employee_attendance[work_entry_type_id.id][employee_id.id]

                    if hr_attendance_id:
                        try:
                            hr_attendance_id.with_context(synch_ignore_constraints=synch_ignore_constraints).write({
                                'check_out': att.timestamp,
                                'device_out_id': att.device_id.id
                            })
                        except ValidationError as e:
                            if att.device_id not in error_msg:
                                error_msg[att.device_id] = ""

                            msg = ""
                            att_check_time = fields.Datetime.context_timestamp(
                                att, att.timestamp)
                            msg += str(e) + "<br />"
                            msg += _("'Check Out' time cannot be earlier than 'Check In' time. Debug information:<br />"
                                     "* Employee: <strong>%s</strong><br />"
                                     "* Type: %s<br />"
                                     "* Attendance Check Time: %s<br />") % (employee_id.name, att.type, fields.Datetime.to_string(att_check_time))
                            _logger.error(msg)
                            error_msg[att.device_id] += msg
                else:
                    # create hr attendance data
                    vals = {
                        'employee_id': employee_id.id,
                        'check_in': att.timestamp,
                        'device_in_id': att.device_id.id,
                        'work_entry_type_id': work_entry_type_id.id,
                    }
                    hr_attendance_id = HrAttendance.search([
                        ('employee_id', '=', employee_id.id),
                        ('check_in', '=', att.timestamp),
                        ('device_in_id', '=', att.device_id.id),
                        ('work_entry_type_id', '=', work_entry_type_id.id)], limit=1)
                    if not hr_attendance_id:
                        try:
                            hr_attendance_id = HrAttendance.create(vals)
                        except Exception as e:
                            _logger.error(e)

                if hr_attendance_id:
                    att.write({
                        'hr_attendance_id': hr_attendance_id.id
                    })

        if bool(error_msg):
            for device in error_msg.keys():

                if not device.debug_message:
                    continue
                device.message_post(body=error_msg[device])

    def clear_attendance(self):
        if not self.device_ids:
            raise (_('You must select at least one device to continue!'))
        if not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
            raise UserError(
                _('Only HR Attendance Managers can manually clear device attendance data'))

        for device in self.device_ids:
            device.clear_attendance()

    def action_fix_user_attendance_valid(self):
        all_attendances = self.env['user.attendance'].search([
            ('timestamp', '>=', str(self.date_from)+' 00:00:00'),
            ('timestamp', '<=', str(self.date_to)+' 23:59:59'),
            ('employee_id', '!=', False),])
        for attendance in all_attendances:
            valid = attendance.is_valid()
            attendance.update({'valid': valid})
