# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _
from dateutil.parser import parse

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    employee_type_id = fields.Many2one(comodel_name='hr.employee.type', 
        string='Employee Type', related='employee_id.employee_type_id', store=True)
    is_late = fields.Boolean(string='Is Late?', default=False)
    attendance_late = fields.Float(string="Late(Minutes)")# compute="get_late_minutes")

    @api.model
    def create(self, vals):
        values = self.check_late(vals.get('employee_id'), vals.get('check_in'))
        if values:
            vals.update(values)
        #     res = super(HrAttendance, self).write(vals)
        # else:
        #     # truong hop nhan vien co hop dong va hop dong o trang thai ['open', 'expiring']
        #     res = super(HrAttendance, self).write(vals)   
        # vals.update(values)
        return super(HrAttendance, self).create(vals)

    def write(self, vals):
        for rec in self:
            if vals.get('check_in'):
                values = rec.check_late(rec.employee_id.id, vals.get('check_in'))
                if values:
                    vals.update(values)
            #         res = super(HrAttendance, self).write(vals)
            # else:
            #     # giong nhu create
            #     res = super(HrAttendance, self).write(vals)
        return super(HrAttendance, self).write(vals)

    def check_late(self,employee, check_in):
        vals = {}
        ob= self.env['erpvn.base']
        if type(check_in) == str:
            employee = self.env['hr.employee'].browse(employee)
            if employee.contract_id and employee.contract_id.state in ['open', 'expiring']:

                convert_check_in=parse(check_in)
                week_day = convert_check_in.weekday()
                work_schedule = employee.contract_id.resource_calendar_id
                schedule = work_schedule.sudo().attendance_ids.filtered(lambda x: x.dayofweek == str(week_day)).sorted('date_from')
                new_time = ob.convert_utc_time_to_tz(convert_check_in,employee.tz).replace(tzinfo=None)
                
                if schedule:
                    range_time = [min(schedule.mapped('hour_from')), max(schedule.mapped('hour_to'))]
                    # convert check_in and range_time to seconds 
                    value = timedelta(hours=range_time[0])
                    range_start = value.total_seconds()

                    value2 = timedelta(hours=range_time[1])
                    range_end = value2.total_seconds()

                    check_in = new_time.time()
                    seconds_check_in = (check_in.hour * 60 + check_in.minute) * 60 + check_in.second
                        
                    # Cần so sánh thời gian check in có nằm trong range_time hay không, nếu có thì xem đi trê bao nhiêu phút.
                    if range_end > seconds_check_in > range_start :
                        result = seconds_check_in - range_start
                        vals.update({
                            'attendance_late': result / 60,
                            'is_late': True,
                        })
                    if seconds_check_in < range_start:
                        result = 0.0
                        vals.update({
                            'attendance_late': result,
                            'is_late': False,
                        })
                    
        return vals

    # def get_late_minutes(self):
    #     for rec in self:
    #         rec.attendance_late = 0.0
    #         week_day = rec.sudo().check_in.weekday()
    #         if rec.employee_id.contract_id:
    #             work_schedule = rec.sudo().employee_id.contract_id.resource_calendar_id
    #             for schedule in work_schedule.sudo().attendance_ids:
    #                 if schedule.dayofweek == str(week_day) and schedule.day_period == 'morning':
    #                     work_from = schedule.hour_from
    #                     result = '{0:02.0f}:{1:02.0f}'.format(*divmod(work_from * 60, 60))

    #                     user_tz = self.env.user.tz
    #                     dt = rec.check_in

    #                     if user_tz in pytz.all_timezones:
    #                         old_tz = pytz.timezone('UTC')
    #                         new_tz = pytz.timezone(user_tz)
    #                         dt = old_tz.localize(dt).astimezone(new_tz)
    #                     str_time = dt.strftime("%H:%M")
    #                     check_in_date = datetime.strptime(str_time, "%H:%M").time()
    #                     start_date = datetime.strptime(result, "%H:%M").time()
    #                     t1 = timedelta(hours=check_in_date.hour, minutes=check_in_date.minute)
    #                     t2 = timedelta(hours=start_date.hour, minutes=start_date.minute)
    #                     if check_in_date > start_date:
    #                         final = t1 - t2
    #                         rec.sudo().write({
    #                             'attendance_late': final.total_seconds() / 60,
    #                             'is_late': True,
    #                         })
                            # rec.sudo().attendance_late = final.total_seconds() / 60

    def attendance_late_records(self):
        existing_records = self.env['hr.attendance.late'].sudo().search([]).attendance_id.ids
        minutes_after = int(self.env['ir.config_parameter'].sudo().get_param('attendance_late_after')) or 0
        max_limit = int(self.env['ir.config_parameter'].sudo().get_param('maximum_minutes')) or 0
        attendance_late_ids = self.sudo().search([('id', 'not in', existing_records)])
        for rec in attendance_late_ids:
            attendance_late = rec.sudo().attendance_late + 210
            if rec.attendance_late > minutes_after and attendance_late > minutes_after and attendance_late < max_limit:
                self.env['hr.attendance.late'].sudo().create({
                    'employee_id': rec.employee_id.id,
                    'late_minutes': attendance_late,
                    'date': rec.check_in.date(),
                    'attendance_id': rec.id,
                })


    def get_attendances(self):
        wz_id =  self.env['attendance.update.wizard'].create({
            'name':'Attendance Update Wizard',
        })
        request_line_obj = self.env['attendance.update.line.wizard']
        vals = []
        for line in self:
            if line.check_in == False or line.check_out == False:
                continue
            else:
                vals.append({
                    'wizard_id': wz_id.id,
                    'employee_id': line.employee_id.id,
                    'employee_barcode': line.employee_barcode,
                    'check_in': line.check_in,
                    'device_in_id': line.device_in_id.id,
                    'check_out': line.check_out,
                    'device_out_id': line.device_out_id.id,
                    'worked_hours': line.worked_hours,
                    'attendance_late':line.attendance_late,
                    'state':line.state,
                })

        if vals:
            request_line_obj.create(vals)
        
        return {
            'name': _('Update Attendances'),
            'view_mode': 'form',
            'view_id': self.env.ref('erpvn_hr_work_entry.attendance_update_wizard_form_view').id,
            'res_model': 'attendance.update.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': wz_id.id,
        }