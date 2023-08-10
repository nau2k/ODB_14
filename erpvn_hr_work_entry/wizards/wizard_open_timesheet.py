# -*- coding: utf-8 -*-
import logging

from datetime import date
from datetime import timedelta
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

from odoo.exceptions import Warning
from odoo import models, fields, exceptions, api, _
from odoo.osv.expression import OR, AND

class WizardOpenTimeSheet(models.TransientModel):
    _name = 'wizard.open.timesheet'
    _description = 'Wizard Open TimeSheet'


    employee_ids = fields.Many2many('hr.employee', string='Employees')
    department_ids = fields.Many2many('hr.department', string='Departments')

    is_employee = fields.Boolean(string='Employee',)
    is_department = fields.Boolean(string='Department',)
    
    date_from = fields.Date(string='Date From',default=fields.Date.context_today,)
    date_to = fields.Date(string='Date To',default=fields.Date.context_today,)


    @api.onchange('department_ids')
    def onchange_department(self):
        domain = {'employee_ids':[]}
        if self.department_ids:
            domain = { 'employee_ids': ['|',('department_id','in',self.department_ids.ids),
                                    ('department_id','child_of',self.department_ids.ids)]}
        else:
            domain = {'employee_ids':[(1,'=',1)]}
        return {'domain': domain}
    

    @api.onchange('is_department','is_employee')
    def onchage_hide_field(self):
        if self.is_department == False:
            self.department_ids = False
        else:
            self.employee_ids = False

    def genarate(self):
        domain = []
        for rec in self:
            if rec.is_department and rec.department_ids:
                domain.append(('department_id','in',rec.department_ids.ids))
            if rec.is_employee and rec.employee_ids:
                domain.append(('employee_id','in',rec.employee_ids.ids))
            if rec.date_from and rec.date_to:
                domain.append(('date_start','>=',rec.date_from))
                domain.append(('date_stop','<=',rec.date_to))

        data =self.env['hr.work.entry'].search(domain)
        if not data:
            raise ValidationError(_('error'))
        docids=self.id
        datas = {
            'form': {'data':data.ids},
        }
        return self.env.ref('erpvn_hr_work_entry.action_report_timesheet').report_action(docids, data=datas,config=False)
    
    def toggle_active(self):
        pass
