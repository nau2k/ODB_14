# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HRAttendance(models.Model):
    _name = 'hr.attendance'
    _inherit = ['hr.attendance', 'mail.thread', 'mail.activity.mixin']

    # ODOO'S FIELDS.
    check_in = fields.Datetime(required=False, tracking=True)
    check_out = fields.Datetime(tracking=True)
    employee_id = fields.Many2one(store=True)
    department_id = fields.Many2one(tracking=True, store=True)

    employee_barcode = fields.Char(related='employee_id.barcode', index=True)
    device_in_id = fields.Many2one('attendance.device', string='Device In', help='The device with which user took check in action')
    device_out_id = fields.Many2one('attendance.device', string='Device Out', help='The device with which user took check out action')
    device_user_id = fields.Many2one('attendance.device.user', string='Device User', ondelete='cascade', index=True, tracking=True)
    type = fields.Selection(selection=[('device', 'Get From Device'), ('user', 'Created By User')], string='Created Type', readonly=True, default='user',
        help='To defined the record was created from device or user.')
    no_check_in = fields.Boolean(string="Is No Check In?")

    description = fields.Text('Description')
    state = fields.Selection(selection=[('draft', 'Draft'), ('cancelled', 'Cancelled'), ('approve', 'Approved'),
        ('no_check_in', 'No Check-In'), ('no_check_out', 'No Check-Out')], string='Status', required=True, tracking=True, default='draft')
    attendance_state_id = fields.Many2one('attendance.state', string='Attendance State', index=True, tracking=True,
        help='This technical field is to map the attendance status stored in the device and the attendance status in Odoo')
    activity_type = fields.Selection(string='Activity Type', related='attendance_state_id.type', store=True)
    device_id = fields.Many2one('attendance.device', string='Attendance Device', tracking=True, ondelete='restrict')
    status = fields.Integer(string='Device Attendance State', tracking=True,
        help='The state which is the unique number stored in the device to indicate type of attendance (e.g. 0: check_in, 1: check_out, etc)')
    work_entry_type_id = fields.Many2one('hr.work.entry.type', index=True)

    def action_set_to_draft(self):
        attendances_to_set_to_draft = self.filtered(lambda x: x.state == 'cancelled')
        if attendances_to_set_to_draft:
            attendances_to_set_to_draft.write({'state': 'draft'})
            return True
        return False

    def action_cancel(self):
        attendances_to_cancel = self.filtered(lambda x: x.state in ('draft', 'no_check_in', 'no_check_out'))
        if attendances_to_cancel:
            attendances_to_cancel.write({'state': 'cancelled'})
            return True
        return False

    def action_validate(self):
        attendances_to_validate = self.filtered(lambda x: x.state == 'draft')
        if attendances_to_validate:
            attendances_to_validate.write({'state': 'approve'})
            return True
        return False

    def action_set_to_draft_multi(self):
        attendances_to_set_to_draft = self.filtered(lambda x: x.state == 'cancelled')
        if attendances_to_set_to_draft:
            attendances_to_set_to_draft.action_set_to_draft()

    def action_cancel_multi(self):
        attendances_to_cancel = self.filtered(lambda x: x.state in ('draft', 'no_check_in', 'no_check_out'))
        if attendances_to_cancel:
            attendances_to_cancel.action_cancel()

    def action_validate_multi(self):
        attendances_to_validate = self.filtered(lambda x: x.state == 'draft')
        if attendances_to_validate:
            attendances_to_validate.action_validate()

    # def _check_attendance(self):
    #     attendances = self.filtered(lambda a: a.check_in > a.check_out)
    #     res_lang = get_lang(self.env, 'en_US')
    #     dt_str_format = res_lang.date_format + ' ' + res_lang.time_format

    #     if attendances:
    #         err_msg = _("Invalid check in/out attendance(s):\n")
    #         for atten in attendances:                
    #             err_msg += _('\t - Employee: %s\t - Check In: %s \t - Check Out: %s\n') % ('[' + str(atten.employee_id.barcode) + '] ' + str(atten.employee_id.name), \
    #                 OdooBase.convert_utc_time_to_tz(atten, atten.check_in).replace(tzinfo=None).strftime(dt_str_format), \
    #                 OdooBase.convert_utc_time_to_tz(atten, atten.check_out).replace(tzinfo=None).strftime(dt_str_format))

    #         raise ValidationError(err_msg)

    #     err_msg = ''
    #     for atten in (self - attendances):
    #         if atten.id == (self - attendances)[:1].id:
    #             err_msg = _("Can not set check out value, the limited range between check in and out is"
    #                 "%s minute(s):\n") % str(self.env.company.attendance_range_in_minutes)

    #         subtraction_range = atten.check_out - atten.check_in
    #         if subtraction_range.days == 0 and subtraction_range.seconds <= (self.env.company.attendance_range_in_minutes * 60):
    #             err_msg += _('\t- %s\t- Check In: %s\t- Check Out: %s\n') % \
    #                 ('[' + str(atten.employee_id.barcode) + '] ' + str(atten.employee_id.name), \
    #                 OdooBase.convert_utc_time_to_tz(atten, atten.check_in).replace(tzinfo=None).strftime(dt_str_format), \
    #                 OdooBase.convert_utc_time_to_tz(atten, atten.check_out).replace(tzinfo=None).strftime(dt_str_format))
    #     if err_msg:
    #         raise ValidationError(err_msg)

    # def write(self, values):
    #     super(HRAttendance, self).write(values)
    #     self.filtered(lambda a: a.check_in and a.check_out)._check_attendance()
    #     return True

    # not use odoo's constraint
    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        pass