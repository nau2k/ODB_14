# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WizardTimeSheetReues(models.TransientModel):
    _name = "wizard.timesheet.adjustment.request"
    _description = "wizard Timesheet Adjustment Request"

    name = fields.Char()
    line_ids = fields.One2many('wizard.timesheet.adjustment.request.line', 'wizard_id', string='Wizard Lines')



    def create_adjustment_request(self):
        request_line_obj = self.env['timesheet.adjustment.request.line']
        for line in self.line_ids:
            line.check_date()
            request_line_record=line.work_entry_id.adjustment_request_ids.filtered(lambda x: x.state == "draft")
            if request_line_record:
                request_line_record[0].update({
                        'new_date_start': line.new_date_start,
                        'new_date_stop': line.new_date_stop,
                    })
                request_line = request_line_record[0]
            else:
                request_line = request_line_obj.create({
                        # 'order_id': line.order_id.id,
                        'employee_id': line.employee_id.id,
                        'work_entry_id': line.work_entry_id.id,
                        'old_date_start': line.old_date_start,
                        'old_date_stop': line.old_date_stop,
                        'old_duration': line.old_duration,
                        'new_date_start': line.new_date_start,
                        'new_date_stop': line.new_date_stop,
                        'break_time':line.break_time,
                    })
                
            request_line.write({'state': 'confirm'})
            request_line.send_noti()

        return request_line

class WizardTimeSheetReuestLine(models.TransientModel):
    _name = "wizard.timesheet.adjustment.request.line"
    _description = "wizard Timesheet Adjustment Request Line"

    wizard_id = fields.Many2one('wizard.timesheet.adjustment.request')
    # active = fields.Boolean(default=True)
    # order_id = fields.Many2one('timesheet.adjustment.request', required=True)
    # sequence = fields.Integer(default=1)
    employee_id = fields.Many2one('hr.employee', default=lambda self: self.env.user.employee_id, required=True, index=True)
    employee_code = fields.Char(related='employee_id.barcode', string='Badge ID', store=True)
    work_entry_id = fields.Many2one('hr.work.entry', string='Adjustment Entry', ondelete='cascade', store=True, required=True)
    # work_entry_type_id = fields.Many2one('hr.work.entry.type', string='Entry Type', store=True)
    # resource_calendar_id = fields.Many2one('resource.calendar', string='Working Shift', store=True)
    # attendance_id = fields.Many2one('resource.calendar.attendance', string='Work Detail', store=True)
    # note = fields.Text(string='Description')
    # company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True, default=lambda self: self.env.company)

    old_date_start = fields.Datetime(store=True, string='Current From')
    old_date_stop = fields.Datetime(store=True, string='Current To')
    old_duration = fields.Float(store=True, string='Current Period')

    new_date_start = fields.Datetime(store=True, string='New From')
    new_date_stop = fields.Datetime( store=True,string='New To')
    new_duration = fields.Float(store=True, string='New Period')

    break_time = fields.Float(string='Break Time', readonly=True)

    def check_date(self):
        for line in self:
            if (line.new_date_start == False or line.new_date_stop== False):
                raise ValidationError(_('"New From" and "New To" cannot be left blank'))
            if line.new_date_start > line.new_date_stop:
                raise ValidationError(_('"New From" not greater than "New To"'))
