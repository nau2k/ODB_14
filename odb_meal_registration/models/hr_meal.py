# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrMeal(models.Model):
    _name = 'hr.meal'
    _description = 'HR Meal'
    _inherit = 'mail.thread'

    name = fields.Char(string='Name')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('approved', 'Approved'),('cancel', 'Cancelled')],  
        default='draft', index=True, copy=False, tracking=True,  string='Status',)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    employee_id = fields.Many2one('hr.employee', string="Responsible",default=lambda self: self.env.user.employee_id.id)
    domain_department_id = fields.Many2many('hr.department', compute= '_compute_domain_department')
    department_id = fields.Many2one('hr.department',string="Department")
    
    date_start = fields.Date('From' ,tracking=True,)
    date_end = fields.Date('To', compute = '_compute_date_end', store=True,tracking=True,)

    description = fields.Char('Description')
    employee_meal_line = fields.One2many('hr.meal.line', 'meal_id', string='Employees', required=True)

    #reset employee line
    @api.onchange('department_id','date_start','date_end')
    def onchange_department_date(self):
        self.employee_meal_line =False

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.department_id:
            self.department_id =False

    # get child department
    @api.depends('employee_id')
    def _compute_domain_department(self):
        for rec in self:
            list_department = self.employee_id.department_id._get_child_departments()
            rec.domain_department_id=False
            if len(list_department)>0:
                rec.domain_department_id = list_department

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                if rec.date_start >= rec.date_end:
                    raise UserError(_('The end date must be greater than or equal to the start date.'))
    
    # @api.constrains('date_start', 'date_end')
    # def _check_dates(self):
    #     for rec in self:
    #         date_config = rec.company_id.limit_date_end or 25
    #         if rec.date_start.month < datetime.today().month or rec.date_end.month < rec.date_start.replace(day=date_config).month:
    #             raise UserError(_('The start date and end date do not meet the required conditions.'))
    
    # set the end date based on the start date and configuration parameter.
    @api.depends('date_start')
    def _compute_date_end(self):
        for rec in self:
            if rec.date_start:
                date_config = rec.company_id.limit_date_end or 25
                rec.date_end = rec.date_start.replace(day=date_config) + relativedelta(months=1) if rec.date_start.day > date_config else rec.date_start.replace(day=date_config)

    def action_confirm(self):
        if not self.employee_meal_line:
            raise UserError(_("Employee field cannot be empty."))
        self.write({'state': 'confirm'})
    
    def action_approve(self):
         self.write({'state': 'approved'})

    def action_cancel(self):
         self.write({'state': 'cancel'})
         self.employee_meal_line.write({'state': 'cancel'})

    def btn_regis_all(self):
        for rec in self.employee_meal_line:
            if not rec.state == 'duplicated':
              rec.write({'is_registry': True})

    def btn_unregis_all(self):
        for rec in self.employee_meal_line:
            if not rec.state == 'duplicated':
               rec.write({'is_registry': False})

    def load_employee(self):
        child_departments = self.department_id._get_child_departments()
        if child_departments:
            employees = self.env['hr.employee'].search([('department_id', 'in', child_departments)])
            if employees:
                for employee in employees:
                    value_emp = {
                        'meal_id': self.id,
                        'employee_id': employee.id,
                        'date_start': self.date_start,
                        'date_end': self.date_end
                    }
                    self.env["hr.meal.line"].sudo().create(value_emp)
            else:
                raise UserError(_("No Employee in Department!"))
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New') and vals.get('date_start'):
            vals['name'] ='MEAL/'+  vals['date_start'].replace('-', '/') + ' - '+ self.env['ir.sequence'].next_by_code('hr.meal')
        return super(HrMeal, self).create(vals)

    def unlink(self):
        if any(rec.state !='draft' for rec in self):
            raise ValidationError(_("You only can delete draft meal!"))
        return super(HrMeal, self).unlink()
