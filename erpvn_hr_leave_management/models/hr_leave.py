# -*- coding: utf-8 -*-
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from datetime import date, datetime, timedelta
from odoo.tools.float_utils import float_round
from pytz import timezone, UTC
from collections import namedtuple, defaultdict
from dateutil.relativedelta import relativedelta
import math

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import float_compare

DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')

class HRLeave(models.Model):
    _inherit = 'hr.leave'

    @api.depends('date_to')
    def compute_return_date(self):
        for order in self:
            if order.date_to:
                date_to = datetime.strptime(
                    str(order.date_to), "%Y-%m-%d %H:%M:%S")
                return_date = date_to + timedelta(days=1)
                order.return_date = return_date.date()

    def _default_get_request_parameters(self, values):
        results = super(HRLeave, self)._default_get_request_parameters(values)
        if results.get('request_unit_custom', False):
            results['request_unit_custom'] = False
        return results

    @api.onchange('holiday_type', 'mode_id', 'employee_id', 'department_id')
    def _onchange_leave_type(self):
        domain = [('valid', '=', True)]
        if self.mode_id:
            domain.append(('mode_id', '=', self.mode_id.id))

            valid_types = self.mode_id.type_ids
            holiday_type = self.mapped('holiday_type')
            if len(holiday_type) == 1 and self.mode_id.code == 'Paid':
                holiday_type = holiday_type[0]
                if holiday_type == 'employee' and self.mapped('employee_id'):
                    for type_id in self.mode_id.type_ids.filtered(lambda x: x.allocation_type != 'no'):
                        mapped_days = type_id.get_employees_days(self.mapped('employee_id').ids)
                        leave_days = mapped_days[self.mapped('employee_id').id][type_id.id]
                        if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) != 1 or float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) != 1:
                            valid_types -= type_id

            domain.append(('id', 'in', valid_types.ids))
            # get default time off in case, mode changed but user don't choose any time off before save.
            if self.holiday_status_id.mode_id != self.mode_id or (valid_types and self.holiday_status_id.id not in valid_types.ids):
                self.holiday_status_id = valid_types[0] if valid_types else False

        return {'domain': {'holiday_status_id': domain}}

    @api.model
    def _get_default_leave_mode_type(self):
        return self.env['hr.leave.mode.type'].search([], limit=1)

    @api.depends('holiday_type')
    def _compute_from_holiday_type(self):
        for holiday in self:
            if holiday.holiday_type == 'employee':
                if not holiday.employee_id:
                    if self.env.context.get('default_employee_id',False) and self.env.user.has_group('erpvn_hr_leave_management.group_hr_holidays_department_user'):
                        holiday.employee_id = self.env['hr.employee'].browse(self.env.context.get('default_employee_id'))
                    else:
                        holiday.employee_id = self.env.user.employee_id
                holiday.mode_company_id = False
                holiday.category_id = False
                holiday.mode_employee_type_id = False
                holiday.leave_employee_ids = False
            elif holiday.holiday_type == 'company':
                holiday.employee_id = False
                if not holiday.mode_company_id:
                    holiday.mode_company_id = self.env.company.id
                
                holiday.mode_employee_type_id = False
                holiday.category_id = False
                holiday.leave_employee_ids = False
            elif holiday.holiday_type == 'department':
                holiday.mode_employee_type_id = False
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.category_id = False
                holiday.leave_employee_ids = False
            elif holiday.holiday_type == 'category':
                holiday.mode_employee_type_id = False
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.leave_employee_ids = False
            elif holiday.holiday_type == 'employee_type':
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.category_id = False
                holiday.leave_employee_ids = False
            else:
                holiday.employee_id = self.env.context.get('default_employee_id') or self.env.user.employee_id

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    sequence = fields.Char(string="Time Off Number", readonly=True, copy=False, default='New', index=True)
    employee_id = fields.Many2one('hr.employee', domain=lambda self: "[('department_id', '=', department_id)]")
    barcode = fields.Char(compute='_compute_employee_barcode', string='Badge ID', store=True)

    allocation_total_display = fields.Char(compute='_compute_employee_allocation', store=True)
    allocation_remained_display = fields.Char(compute='_compute_employee_allocation', store=True)
    allocation_taken_display = fields.Char(compute='_compute_employee_allocation', store=True)

    image_1920 = fields.Image(related='employee_id.image_1920')

    mode_id = fields.Many2one(string='Mode Type', comodel_name='hr.leave.mode.type',ondelete='restrict', default=_get_default_leave_mode_type)
    return_date = fields.Date("Return Date", compute="compute_return_date", store=True)
    holiday_status_id = fields.Many2one(domain=_onchange_leave_type)
    type_description = fields.Html(string='Type Description', related='holiday_status_id.description')

    request_hour_from = fields.Selection(selection_add=[
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
        ('23', '23:00'), ('23.25', '23:15'), ('23.5', '23:30'), ('23.75', '23:45')], string='Hour From')

    request_hour_to = fields.Selection(selection_add=[
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
        ('23', '23:00'), ('23.25', '23:15'), ('23.5', '23:30'), ('23.75', '23:45')], string='Hour To')

    private_name = fields.Char('Time Off Description', groups='hr_holidays.group_hr_holidays_user,erpvn_hr_leave_management.group_hr_holidays_department_manager')
    confirmed_date = fields.Datetime(string='Confirmed Date', store=True, readonly=True)

    holiday_type = fields.Selection(selection_add=[
        ('employee_type', 'Employee Type'),
        ('employee_cus', 'Employee Customized'),
    ], ondelete={'employee_type': 'cascade', 'employee_cus': 'cascade'})
    mode_employee_type_id = fields.Many2one('hr.employee.type', string="Employee Type")
    
    leave_employee_ids = fields.One2many('hr.leave.employee.list', 'hr_leave_id', string='Employee List')
    customize_leave_type = fields.Selection([
        ('normal', 'Normal'),
        ('interrupted', 'Interrupted Range')], default='normal',
        help="The 'Interrupted Range' is used for creating multiple range leaves.")
    cus_employee_id = fields.Many2one(string='Customized Employee', comodel_name='hr.employee')

    # override odoo's _sql_constraints.
    _sql_constraints = [
        ('type_value',
         "CHECK((holiday_type='employee' AND customize_leave_type='normal' AND employee_id IS NOT NULL) or "
         "(holiday_type='employee_cus' AND cus_employee_id IS NOT NULL) or "
         "(holiday_type='company' AND mode_company_id IS NOT NULL) or "
         "(holiday_type='category' AND category_id IS NOT NULL) or "
         "(holiday_type='department' AND department_id IS NOT NULL) or "
         "(holiday_type='employee_type' AND mode_employee_type_id IS NOT NULL) )",
         "The employee, department, company, employee type or employee category of this request is missing. Please make sure that your user login is linked to an employee."),
    ]

    @api.depends('employee_id', 'cus_employee_id')
    def _compute_employee_allocation(self):
        for holiday in self.filtered(lambda x: x.employee_id or x.cus_employee_id):
            employee_id = holiday.employee_id if holiday.employee_id else holiday.cus_employee_id 
            holiday.allocation_total_display = employee_id.allocation_total_display
            holiday.allocation_remained_display = employee_id.allocation_remained_display
            holiday.allocation_taken_display = employee_id.allocation_taken_display

    @api.onchange('customize_leave_type')
    def _compute_customize_leave_type(self):
        for holiday in self:
            if holiday.customize_leave_type != 'normal' and holiday.holiday_type == 'employee':
                holiday.holiday_type = 'employee_cus'
                holiday.cus_employee_id = holiday.employee_id
                holiday.employee_id = False
            elif holiday.customize_leave_type == 'normal' and holiday.cus_employee_id == 'employee' and holiday.holiday_type == 'employee':
                holiday.employee_id = holiday.cus_employee_id

    @api.depends('employee_id', 'holiday_type')
    def _compute_department_id(self):
        super(HRLeave, self)._compute_department_id()

        for holiday in self.filtered(lambda x: x.cus_employee_id and not x.employee_id):
            holiday.department_id = holiday.cus_employee_id.department_id

    @api.depends('employee_id')
    def _compute_employee_barcode(self):
        for holiday in self:
            holiday.barcode = holiday.employee_id.barcode if holiday.employee_id.barcode else ''
    
    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if not values.get('employee_id', False) and values.get('holiday_type', '') == 'employee':
                raise UserError(_('Employee is required.'))
                
            leave_code = ''
            if values.get('holiday_type', '') == 'employee':
                leave_code = self.env['hr.employee'].sudo().browse(values.get('employee_id')).barcode or self.env['hr.employee'].sudo().browse(values.get('employee_id')).name or ''
            elif values.get('holiday_type', '') == 'department':
                leave_code = self.env['hr.department'].sudo().browse(values.get('department_id')).code or ''
            sequence = "LEAVE/" + leave_code + "/" + self.env['ir.sequence'].next_by_code('hr.leavve.sequence')
            values['sequence'] = sequence or _('New')

            if values.get('state', '') == 'confirm':
                values['confirmed_date'] = datetime.now()

        res = super().create(vals_list)

        # send mail in case the holiday in state "confirm"
        template_id = self.env.ref('erpvn_hr_leave_management.leave_request_mail')
        for holiday in res.filtered(lambda x: x.state == 'confirm' and x.holiday_type == 'employee'):
            template_id.send_mail(holiday.id, force_send=True)

        return res

    def write(self, values):
        
        if self.env.context.get('update_department_manager', False):
            return super(HRLeave, self).write(values)

        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.is_superuser()
        is_department_manager = self.user_has_groups('erpvn_hr_leave_management.group_hr_holidays_department_manager') and \
            self.department_id.id in self.env.user.department_id._get_child_departments()
        is_manager = self.employee_id.parent_id == self.env.user.employee_id

        if not bool(is_officer or is_department_manager or is_manager) and values.keys() - {'message_main_attachment_id'}:
            if any(hol.date_from.date() < fields.Date.today() and hol.employee_id.leave_manager_id != self.env.user for hol in self):
                raise UserError(_('You must have manager rights to modify/validate a time off that already begun'))

        employee_id = values.get('employee_id', False) or self.employee_id.id
        if not self.env.context.get('leave_fast_create'):
            if values.get('state'):
                self._check_approval_update(values['state'])
                if any(holiday.validation_type == 'both' for holiday in self):
                    if values.get('employee_id'):
                        employees = self.env['hr.employee'].browse(values.get('employee_id'))
                    else:
                        employees = self.mapped('employee_id')
                    # self._check_double_validation_rules(employees, values['state'])
                    if values.get('state') == 'validate1':
                        employees = employees.filtered(lambda employee: employee.leave_manager_id != self.env.user)
                        if employees and not bool(is_officer or is_department_manager):
                            raise AccessError(_('You cannot first approve a time off for %s, because you are not his time off manager', employees[0].name))
                    elif values.get('state') == 'validate' and not bool(is_officer or is_department_manager):
                        # Is probably handled via ir.rule
                        raise AccessError(_('You don\'t have the rights to apply second approval on a time off request'))
            if 'date_from' in values:
                values['request_date_from'] = values['date_from']
            if 'date_to' in values:
                values['request_date_to'] = values['date_to']
        # result = super(HRLeave, self.with_user(SUPERUSER_ID).sudo()).write(values)
        result = super(HRLeave, self.sudo()).write(values)
        if not self.env.context.get('leave_fast_create'):
            for holiday in self:
                if employee_id:
                    holiday.add_follower(employee_id)
        return result

    def _check_double_validation_rules(self, employees, state):
        if self.user_has_groups('hr_holidays.group_hr_holidays_manager') or self.user_has_groups('erpvn_hr_leave_management.group_hr_holidays_department_manager') or self.env.is_superuser():
            return
        
        is_department_manager = self.user_has_groups('erpvn_hr_leave_management.group_hr_holidays_department_manager') and \
            self.department_id.id in self.env.user.department_id._get_child_departments()

        if state == 'validate1':
            employees = employees.filtered(lambda employee: employee.leave_manager_id != self.env.user)
            if employees and not is_department_manager:
                raise AccessError(_('You cannot first approve a time off for %s, because you are not his time off manager', employees[0].name))
        elif state == 'validate' and not is_department_manager:
            # Is probably handled via ir.rule
            raise AccessError(_('You don\'t have the rights to apply second approval on a time off request'))

    @api.depends('state', 'employee_id', 'department_id')
    def _compute_can_approve(self):
        for holiday in self:
            if self.user_has_groups('erpvn_hr_leave_management.group_hr_holidays_department_manager'):
                holiday.can_approve = True
            else:
                try:
                    if holiday.state == 'confirm' and holiday.validation_type == 'both':
                        holiday._check_approval_update('validate1')
                    else:
                        holiday._check_approval_update('validate')
                except (AccessError, UserError):
                    holiday.can_approve = False
                else:
                    holiday.can_approve = True

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return

        current_employee = self.env.user.employee_id
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_administrator = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        is_department_manager = self.user_has_groups('erpvn_hr_leave_management.group_hr_holidays_department_manager') and \
            self.department_id.id in self.env.user.department_id._get_child_departments() or \
            self.employee_id.parent_id == self.env.user.employee_id

        for holiday in self:
            val_type = holiday.validation_type

            if not is_administrator and state != 'confirm':
                if state == 'draft':
                    if holiday.state == 'refuse':
                        raise UserError(_('Only a Time Off Manager can reset a refused leave.'))
                    if holiday.date_from and holiday.date_from.date() <= fields.Date.today():
                        raise UserError(_('Only a Time Off Manager can reset a started leave.'))
                    if holiday.employee_id != current_employee:
                        raise UserError(_('Only a Time Off Manager can reset other people leaves.'))
                else:
                    if val_type == 'no_validation' and current_employee == holiday.employee_id:
                        continue
                    # use ir.rule based first access check: department, members, ... (see security.xml)
                    holiday.check_access_rule('write')

                    # This handles states validate1 validate and refuse
                    if holiday.employee_id == current_employee:
                        raise UserError(_('Only a Time Off Manager can approve/refuse its own requests.'))

                    if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager') and holiday.holiday_type == 'employee':
                        if not is_officer and self.env.user != holiday.employee_id.leave_manager_id:
                            if not is_department_manager:
                                raise UserError(_('You must be either %s\'s manager or Time off Manager to approve this leave') % (holiday.employee_id.name))

                    if not is_officer and (state == 'validate' and val_type == 'hr') and holiday.holiday_type == 'employee':
                        raise UserError(_('You must either be a Time off Officer or Time off Manager to approve this leave'))

    @api.depends_context('uid')
    def _compute_description(self):
        self.check_access_rights('read')
        self.check_access_rule('read')

        is_officer = self.user_has_groups('hr_holidays.group_hr_holidays_user')
        is_department_user = self.user_has_groups('erpvn_hr_leave_management.group_hr_holidays_department_user')

        for leave in self:
            is_manager = leave.employee_id.parent_id == self.env.user.employee_id
            if is_officer or leave.user_id == self.env.user or leave.employee_id.leave_manager_id == self.env.user or is_department_user or is_manager:
                leave.name = leave.sudo().private_name
            else:
                leave.name = '*****'

    def _inverse_description(self):
        is_department_user = self.user_has_groups('erpvn_hr_leave_management.group_hr_holidays_department_user')
        # is_department_manager = self.user_has_groups('erpvn_hr_leave_management.group_hr_holidays_department_manager')
        is_manager = self.employee_id.parent_id == self.env.user.employee_id
        is_officer = self.user_has_groups('hr_holidays.group_hr_holidays_user')

        for leave in self:
            # if is_officer or leave.user_id == self.env.user or leave.employee_id.leave_manager_id == self.env.user or is_department_manager or is_manager:
            if is_officer or leave.user_id == self.env.user or leave.employee_id.leave_manager_id == self.env.user or is_department_user or is_manager:
                leave.sudo().private_name = leave.name
            # elif is_department_user:
            #     if leave.sudo().private_name:
            #         leave.sudo().private_name = leave.sudo().private_name + '\n' + leave.name
            #     else:
            #         leave.sudo().private_name = leave.name


    def action_confirm(self):
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Time off request must be in Draft state ("To Submit") in order to confirm it.'))
        template_id = self.env.ref(
            'erpvn_hr_leave_management.leave_request_mail')
        template_id.send_mail(self.id, force_send=True)
        self.write({'state': 'confirm', 'confirmed_date': datetime.now()})
        return True

    def action_approve(self):
        res = super(HRLeave, self).action_approve()
        template_id = self.env.ref(
            'erpvn_hr_leave_management.leave_approval_mail')
        template_id.send_mail(self.id, force_send=True)
        return res

    def action_refuse(self):
        requests_to_refuse = self.filtered(lambda x: x.state in ['draft', 'confirm', 'validate1'])
        res = super(HRLeave, self).action_refuse()
        
        if not self._context.get('skip_send_mail', False):
            for holiday in requests_to_refuse:
                template_id = self.env.ref('erpvn_hr_leave_management.leave_rejection_mail')
                template_id.send_mail(holiday.id, force_send=True)

        return res

    def _get_number_of_days(self, date_from, date_to, employee_id):
        result = super(HRLeave, self)._get_number_of_days(date_from, date_to, employee_id)

        if employee_id and self.request_unit_half and result['hours'] > 0:
            from_datetime = self.env['erpvn.base'].convert_utc_time_to_tz(date_from, self.tz)
            to_datetime = self.env['erpvn.base'].convert_utc_time_to_tz(date_to, self.tz)

            employee = self.env['hr.employee'].browse(employee_id)
            intervals = employee.resource_calendar_id._work_intervals_batch(from_datetime, to_datetime, employee.resource_id)[employee.resource_id.id]
            for start, stop, attendance in intervals:
                if attendance.break_time_ids:
                    break_id = attendance.break_time_ids[0]
                    hours = break_id.hour_from - (from_datetime.time().hour + from_datetime.time().minute/60)
                    if self.request_date_from_period == 'pm':
                        hours = (to_datetime.time().hour + to_datetime.time().minute/60) - break_id.hour_to
                        
                    if hours > 0.0:
                        result['hours'] = hours
                        break
        return result

    # override odoo's func.
    @api.depends('number_of_days')
    def _compute_number_of_hours_display(self):
        for holiday in self:
            calendar = holiday._get_calendar()
            if holiday.date_from and holiday.date_to:
                if holiday.state == 'validate':
                    start_dt = holiday.date_from
                    end_dt = holiday.date_to
                    if not start_dt.tzinfo:
                        start_dt = start_dt.replace(tzinfo=UTC)
                    if not end_dt.tzinfo:
                        end_dt = end_dt.replace(tzinfo=UTC)
                    resource = holiday.employee_id.resource_id
                    intervals = calendar._attendance_intervals_batch(start_dt, end_dt, resource)[resource.id] \
                                - calendar._leave_intervals_batch(start_dt, end_dt, None)[False]  # Substract Global Leaves
                    number_of_hours = sum(((stop - start).total_seconds() / 3600) - calendar._get_breaking_hours(dummy, start, stop)  for start, stop, dummy in intervals)
                else:
                    number_of_hours = holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['hours']
                holiday.number_of_hours_display = number_of_hours or (holiday.number_of_days * (calendar.hours_per_day or HOURS_PER_DAY))
            else:
                holiday.number_of_hours_display = 0

    @api.depends('employee_id')
    def _compute_from_employee_id(self):
        """ Override odoo function. """
        return

    @api.model
    def update_allocation_for_formers(self):
        ACCURAL_YEARS = 5
        allocation_vals = []
        holiday_status_id = self.env['hr.leave.type'].sudo().search([('code', '=', 'ANPL')], limit=1)
        for employee in self.env['hr.employee'].search([('employee_type_id.name', 'in', ('Factory', 'Office')), ('joining_date', '!=', False)]):
            num_of_days = int((date.today() - employee.joining_date).days / (ACCURAL_YEARS * 365))
            if num_of_days > 0:
                allocation_vals.append({
                    'employee_id': employee.id,
                    'state': 'validate',
                    'holiday_status_id': holiday_status_id.id,
                    'number_of_days': num_of_days,
                    'notes': _('Add %s day(s) for %s year(s) working.') \
                        % (str(num_of_days), str(num_of_days * ACCURAL_YEARS)),
                })
                employee.seniority_leave = num_of_days

        self.env['hr.leave.allocation'].with_user(SUPERUSER_ID).create(allocation_vals)
        return True

    # override odoo's func
    def action_validate(self):
        current_employee = self.env.user.employee_id
        leaves = self.filtered(lambda l: l.employee_id and not l.number_of_days)
        if leaves:
            raise ValidationError(_('The following employees are not supposed to work during that period:\n %s') % ','.join(leaves.mapped('employee_id.name')))

        if any(holiday.state not in ['confirm', 'validate1'] and holiday.validation_type != 'no_validation' for holiday in self):
            raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})
        self.filtered(lambda holiday: holiday.validation_type == 'both').write({'second_approver_id': current_employee.id})
        self.filtered(lambda holiday: holiday.validation_type != 'both').write({'first_approver_id': current_employee.id})

        for holiday in self.filtered(lambda holiday: holiday.holiday_type != 'employee'):
            leave_employees = holiday.leave_employee_ids.filtered(lambda x: x.status in ['valid', 'diff'])

            leaves = self.env['hr.leave'].with_context(
                tracking_disable=True,
                mail_activity_automation_skip=True,
                leave_fast_create=True,
                leave_skip_state_check=True,
                holiday_type=self.holiday_type,
            ).create([{
                'name': leav_employee.name,
                'holiday_type': 'employee',
                'holiday_status_id': leav_employee.hr_leave_type_id.id,
                'date_from': leav_employee.date_from,
                'date_to': leav_employee.date_to,
                'request_date_from': leav_employee.request_date_from,
                'request_date_to': leav_employee.request_date_to,
                'notes': leav_employee.notes,
                'number_of_days': leav_employee.number_of_days,
                'parent_id': leav_employee.parent_id.id,
                'employee_id': leav_employee.employee_id.id,
                'state': 'validate',
            } for leav_employee in leave_employees if leav_employee.number_of_days])

            leaves._validate_leave_request()

        employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
        employee_requests._validate_leave_request()
        if not self.env.context.get('leave_fast_create'):
            employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()

        return True

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        if (self.env.context.get('holiday_type', False) and self.env.context.get('holiday_type') != 'employee') or \
            bool(self.filtered(lambda x: x.customize_leave_type != 'normal')):
            mapped_days = self.mapped('holiday_status_id').get_employees_days(self.mapped('employee_id').ids)
            for holiday in self:
                if holiday.holiday_type != 'employee' or not holiday.employee_id or \
                    holiday.holiday_status_id.allocation_type == 'no' or \
                    holiday.customize_leave_type != 'normal':
                    continue
                leave_days = mapped_days[holiday.employee_id.id][holiday.holiday_status_id.id]
                if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                    holiday.update({'holiday_status_id': self.env.company.unpaid_holiday_status_id.id})
        else:
            super(HRLeave, self)._check_holidays()

    def get_receiver(self, employee):
        res = employee.name
        contact_id = self.env['res.partner'].search([('employee_id', '=', employee.id), \
            ('company_id', '=', self.env.company.id)], limit=1)

        if contact_id.title:
            res = contact_id.title.name + '. ' + res
        return res

    def get_receiver_email(self, employee):
        return employee.work_email

    def get_duration_display_for_mail(self):
        res = str(round(self.number_of_days, 2)) + ' days'

        if self.number_of_days:
            duration_type = self.holiday_status_id.request_unit

            if duration_type == 'hour':
                total_hours = self.number_of_days * HOURS_PER_DAY
                res = str(total_hours)
                if not (total_hours > 0) and self.number_of_hours_display:
                    res = str(round(self.number_of_hours_display, 2))
                res += ' hours' if total_hours > 1 else ' hour'
            elif duration_type == 'day':
                res = str(round(self.number_of_days, 2))
                res += ' days' if self.number_of_days > 1 else ' day'

        return res

    def get_type(self):
        if self.holiday_type == 'employee':
            return 'Employee'
        elif self.holiday_type == 'department':
            return 'Department'

    def get_type_value(self):
        if self.holiday_type == 'employee':
            return self.employee_id.name
        elif self.holiday_type == 'department':
            return self.department_id.name

    def get_description(self):
        return self.name or ''

    @api.model
    def check_expired_holiday_requests(self):
        holidays = self.env['hr.leave'].sudo().search([('state', 'in', ('draft', 'confirm')), ('holiday_type', '=', 'employee')])

        holidays_to_make_twice_remind = holidays.filtered(lambda x: (datetime.now() - x.create_date).days == 2)

        holidays_to_refuse = (holidays - holidays_to_make_twice_remind).filtered(lambda x: \
            x.confirmed_date and (datetime.now() - x.confirmed_date).days >= 3 \
            or not x.confirmed_date and (datetime.now() - x.create_date).days >= 3)

        dict_val = defaultdict(lambda: self.env['hr.leave'])
        for manager in holidays_to_make_twice_remind.mapped('employee_id.parent_id'):
            dict_val[manager] = holidays_to_make_twice_remind.filtered(lambda x: x.employee_id.parent_id.id == manager.id)

        for manager, records in dict_val.items():
            ctx = defaultdict(list)
            ctx['data'] = records
            user_ids = manager.user_id
            if user_ids:
                template_id = self.env.ref('erpvn_hr_leave_management.leave_request_mail_remind')
                template_id.with_context(ctx).send_mail(records[-1].id, force_send=True, notif_layout=False)

        for holiday in holidays_to_refuse:
            template_id = self.env.ref('erpvn_hr_leave_management.leave_rejection_mail_automatically')
            template_id.send_mail(holiday.id, force_send=True, notif_layout=False)

        for hol in holidays_to_refuse:
            hol.write({'state': 'cancel'})
        return True

    def _get_date_range_employee(self, employee_id):
        self.ensure_one()

        resource_calendar_id = employee_id.resource_calendar_id or self.env.company.resource_calendar_id
        domain = [('calendar_id', '=', resource_calendar_id.id), ('display_type', '=', False)]
        attendances = self.env['resource.calendar.attendance'].read_group(domain, ['ids:array_agg(id)', 'hour_from:min(hour_from)', 'hour_to:max(hour_to)', 'week_type', 'dayofweek', 'day_period'], ['week_type', 'dayofweek', 'day_period'], lazy=False)

        # Must be sorted by dayofweek ASC and day_period DESC
        attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'], group['day_period'], group['week_type']) for group in attendances], key=lambda att: (att.dayofweek, att.day_period != 'morning'))

        default_value = DummyAttendance(0, 0, 0, 'morning', False)

        if resource_calendar_id.two_weeks_calendar:
            # find week type of start_date
            start_week_type = int(math.floor((self.request_date_from.toordinal() - 1) / 7) % 2)
            attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == start_week_type]
            attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != start_week_type]
            # First, add days of actual week coming after date_from
            attendance_filtred = [att for att in attendance_actual_week if int(att.dayofweek) >= self.request_date_from.weekday()]
            # Second, add days of the other type of week
            attendance_filtred += list(attendance_actual_next_week)
            # Third, add days of actual week (to consider days that we have remove first because they coming before date_from)
            attendance_filtred += list(attendance_actual_week)

            end_week_type = int(math.floor((self.request_date_to.toordinal() - 1) / 7) % 2)
            attendance_actual_week = [att for att in attendances if att.week_type is False or int(att.week_type) == end_week_type]
            attendance_actual_next_week = [att for att in attendances if att.week_type is False or int(att.week_type) != end_week_type]
            attendance_filtred_reversed = list(reversed([att for att in attendance_actual_week if int(att.dayofweek) <= self.request_date_to.weekday()]))
            attendance_filtred_reversed += list(reversed(attendance_actual_next_week))
            attendance_filtred_reversed += list(reversed(attendance_actual_week))

            # find first attendance coming after first_day
            attendance_from = attendance_filtred[0]
            # find last attendance coming before last_day
            attendance_to = attendance_filtred_reversed[0]
        else:
            # find first attendance coming after first_day
            attendance_from = next((att for att in attendances if int(att.dayofweek) >= self.request_date_from.weekday()), attendances[0] if attendances else default_value)
            # find last attendance coming before last_day
            attendance_to = next((att for att in reversed(attendances) if int(att.dayofweek) <= self.request_date_to.weekday()), attendances[-1] if attendances else default_value)

        compensated_request_date_from = self.request_date_from
        compensated_request_date_to = self.request_date_to

        hour_from = float_to_time(float(self.request_hour_from))
        hour_to = float_to_time(float(self.request_hour_to))
        if self.customize_leave_type == 'normal':
            if self.request_unit_half:
                if self.request_date_from_period == 'am':
                    hour_from = float_to_time(attendance_from.hour_from)
                    hour_to = float_to_time(attendance_from.hour_to)
                else:
                    hour_from = float_to_time(attendance_to.hour_from)
                    hour_to = float_to_time(attendance_to.hour_to)
            elif self.request_unit_hours:
                hour_from = float_to_time(float(self.request_hour_from))
                hour_to = float_to_time(float(self.request_hour_to))
            elif self.request_unit_custom:
                hour_from = self.date_from.time()
                hour_to = self.date_to.time()
                compensated_request_date_from = self._adjust_date_based_on_tz(self.request_date_from, hour_from)
                compensated_request_date_to = self._adjust_date_based_on_tz(self.request_date_to, hour_to)
            else:
                hour_from = float_to_time(attendance_from.hour_from)
                hour_to = float_to_time(attendance_to.hour_to)

        date_from = timezone(self.tz).localize(datetime.combine(compensated_request_date_from, hour_from)).astimezone(UTC).replace(tzinfo=None)
        date_to = timezone(self.tz).localize(datetime.combine(compensated_request_date_to, hour_to)).astimezone(UTC).replace(tzinfo=None)

        return date_from, date_to
    

    def _get_leave_employee(self, employee, date_from, date_to, mapped_days):
        if not (employee and date_from and date_to):
            return {}
        
        vals = {
            'name': 'Not working on this duration',
            'hr_leave_type_id': False,
            'date_from': date_from,
            'date_to': date_to,
            'request_date_from': date_from.date(),
            'request_date_to': date_to.date(),
            'notes': 'Not working on this duration',
            'number_of_days': 0.0,
            'number_of_hours': 0.0,
            'duration_display': '',
            'parent_id': self.id,
            'hr_leave_id': self.id,
            'employee_id': employee.id,
            'state': 'draft',
            'status': 'unwork',
        }
        
        work_days_data = employee._get_work_days_data_batch(date_from, date_to)

        if self.holiday_status_id.allocation_type == 'no':
            duration_display = '%g %s' % (
                (float_round(work_days_data[employee.id]['days'] * HOURS_PER_DAY if not work_days_data[employee.id].get('hours', False) else work_days_data[employee.id]['hours'], precision_digits=2)
                if self.leave_type_request_unit == 'hour'
                else float_round(work_days_data[employee.id]['days'], precision_digits=2)),
                _('hours') if self.leave_type_request_unit == 'hour' else _('days'))

            if work_days_data[employee.id]['days']:
                vals = {
                    'name': self.name,
                    'hr_leave_type_id': self.holiday_status_id.id,
                    'date_from': date_from,
                    'date_to': date_to,
                    'request_date_from': date_from.date(),
                    'request_date_to': date_to.date(),
                    'notes': self.notes,
                    'number_of_days': work_days_data[employee.id]['days'],
                    'number_of_hours': work_days_data[employee.id]['days'] * HOURS_PER_DAY,
                    'duration_display': duration_display,
                    'parent_id': self.id,
                    'hr_leave_id': self.id,
                    'employee_id': employee.id,
                    'state': 'draft',
                    'status': 'valid',
                }

            return vals
    

        conflicting_leaves = self.env['hr.leave'].with_context(
            tracking_disable=True,
            mail_activity_automation_skip=True,
            leave_fast_create=True
        ).search([
            ('date_from', '<=', date_to),
            ('date_to', '>', date_from),
            ('state', 'not in', ['cancel', 'refuse']),
            ('holiday_type', '=', 'employee'),
            ('employee_id', '=', employee.id)])

        if conflicting_leaves:
            if self.leave_type_request_unit != 'day' or any(l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
                vals.update({
                    'name': 'Have another time off that overlaps on the same day.',
                    'notes': 'Have another time off that overlaps on the same day.',
                    'status': 'duplicated',
                })

                return vals

        if work_days_data[employee.id]['days']:
            duration_display = '%g %s' % (
                (float_round(work_days_data[employee.id]['days'] * HOURS_PER_DAY if not work_days_data[employee.id].get('hours', False) else work_days_data[employee.id]['hours'], precision_digits=2)
                if self.leave_type_request_unit == 'hour'
                else float_round(work_days_data[employee.id]['days'], precision_digits=2)),
                _('hours') if self.leave_type_request_unit == 'hour' else _('days'))

            vals = {
                'name': self.name,
                'hr_leave_type_id': self.holiday_status_id.id,
                'date_from': date_from,
                'date_to': date_to,
                'request_date_from': date_from.date(),
                'request_date_to': date_to.date(),
                'notes': self.notes,
                'number_of_days': work_days_data[employee.id]['days'],
                'number_of_hours': work_days_data[employee.id]['days'] * HOURS_PER_DAY,
                'duration_display': duration_display,
                'parent_id': self.id,
                'hr_leave_id': self.id,
                'employee_id': employee.id,
                'state': 'draft',
                'status': 'valid',
            }
            leave_days = mapped_days[employee.id][self.holiday_status_id.id]
            if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) <= 0 or float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) <= 0:
                vals.update({
                    'hr_leave_type_id': self.env.company.unpaid_holiday_status_id.id,
                    'status': 'diff',
                })

        return vals

    def compute_sheet(self):
        self.ensure_one()

        self.write({'leave_employee_ids': [(6, 0, [])]})
        employees = self.env['hr.employee']
        domain = [('barcode', '!=', False)]

        if self.holiday_type == 'company':
            domain += [('company_id', '=', self.mode_company_id.id)]
            employees = self.env['hr.employee'].search(domain)
        elif self.holiday_type == 'employee_type':
            domain += [('employee_type_id', '=', self.mode_employee_type_id.id)]
            employees = self.env['hr.employee'].search(domain)
        elif self.holiday_type == 'department':
            employees = self.department_id.member_ids.filtered(lambda x: x.barcode)
        elif self.holiday_type == 'category':
            employees = self.category_id.employee_ids.filtered(lambda x: x.barcode)
        elif self.holiday_type == 'employee_cus':
            employees = self.cus_employee_id

        employee_leave_vals = []
        mapped_days = self.mapped('holiday_status_id').get_employees_days(employees.ids)
        for employee in employees:
            paid_leave_hours = 0
            if self.customize_leave_type != 'normal':
                run_date = self.request_date_from
                while run_date <= self.request_date_to:
                    date_from = timezone(self.tz).localize(datetime.combine(run_date, float_to_time(float(self.request_hour_from)))).astimezone(UTC).replace(tzinfo=None)
                    date_to = timezone(self.tz).localize(datetime.combine(run_date, float_to_time(float(self.request_hour_to)))).astimezone(UTC).replace(tzinfo=None)
                    leave_val = self._get_leave_employee(employee, date_from, date_to, mapped_days)
                    if leave_val:

                        if self.holiday_status_id.allocation_type != 'no':
                            paid_leave_hours += leave_val['number_of_hours']
                            leave_days = mapped_days[employee.id][self.holiday_status_id.id]
                            remaining_leaves = leave_days['remaining_leaves'] - paid_leave_hours
                            virtual_remaining_leaves = leave_days['virtual_remaining_leaves'] - paid_leave_hours
                            if float_compare(remaining_leaves, 0, precision_digits=2) <= 0 or float_compare(virtual_remaining_leaves, 0, precision_digits=2) <= 0:
                                leave_val.update({
                                    'hr_leave_type_id': self.env.company.unpaid_holiday_status_id.id,
                                    'status': 'diff',
                                })
                                
                        employee_leave_vals.append(leave_val)

                    run_date += relativedelta(days=1)
            else:
                leave_val = self._get_leave_employee(employee, self.date_from, self.date_to, mapped_days)
                if leave_val:
                    employee_leave_vals.append(leave_val)

        seq = 1
        for val in employee_leave_vals:
            val['sequence'] = seq
            seq += 1
        self.env['hr.leave.employee.list'].create(employee_leave_vals)

    @api.onchange('leave_employee_ids')
    def _onchange_employee_ids(self):
        for rec in self.filtered(lambda x: x.leave_employee_ids):
            seq = 1
            for l in rec.leave_employee_ids:
                l.sequence = seq
                seq += 1
    
    @api.depends('request_date_from_period', 'request_hour_from', 'request_hour_to', 'request_date_from', 'request_date_to',
                'request_unit_half', 'request_unit_hours', 'request_unit_custom', 'employee_id')
    def _compute_date_from_to(self):
        normal_holidays = self.filtered(lambda x: x.customize_leave_type == 'normal')

        for holiday in self - normal_holidays:
            if holiday.request_date_from and holiday.request_date_to and holiday.request_date_from > holiday.request_date_to:
                holiday.request_date_to = holiday.request_date_from
            if not holiday.request_date_from:
                holiday.date_from = False
            elif not holiday.request_date_to:
                holiday.date_to = False
            else:
                compensated_request_date_from = holiday.request_date_from
                compensated_request_date_to = holiday.request_date_to
                hour_from = float_to_time(float(holiday.request_hour_from))
                hour_to = float_to_time(float(holiday.request_hour_to))


                holiday.date_from = timezone(holiday.tz).localize(datetime.combine(compensated_request_date_from, hour_from)).astimezone(UTC).replace(tzinfo=None)
                holiday.date_to = timezone(holiday.tz).localize(datetime.combine(compensated_request_date_to, hour_to)).astimezone(UTC).replace(tzinfo=None)
        
        super(HRLeave, normal_holidays)._compute_date_from_to()

    def save_with_interrupted(self):
        pass