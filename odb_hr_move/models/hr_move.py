# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrMove(models.Model):
    _name = 'hr.move'
    _description = 'HR move'
    _inherit = 'mail.thread'

    name = fields.Char(string='Name')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),('approved', 'Approved'), ('cancel', 'Cancelled')],default='draft',index=True,copy=False,  tracking=True,string='Status',)
    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company)
    
    responsible_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    transfered_date = fields.Date('Transfered Date')
    
    #now
    employee_id = fields.Many2one('hr.employee',  string="Employee")

    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id", store=True)
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id", store=True)
    title_id = fields.Many2one(string='Job Title', comodel_name='hr.job.title', related="employee_id.title_id", store=True)
    job_title = fields.Char("Job Title (Eng)", related="employee_id.job_title", store=True)
    
    #move
    new_department_id = fields.Many2one('hr.department', string="New Department")
    new_job_id = fields.Many2one('hr.job', string="Job")
    new_title_id = fields.Many2one(string='Job Title', comodel_name='hr.job.title')
    new_job_title = fields.Char("Job Title (Eng)", store=True)
    
    reason = fields.Text('Reason')


    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.new_department_id = self.department_id if self.department_id else False
            self.new_job_id = self.job_id if self.job_id else False
            self.new_title_id = self.title_id if self.title_id else False
            self.new_job_title = self.job_title if self.job_title else False


    def action_confirm(self):
        # template_id = self.env.ref('odb_meal_registration.approve_meal_registration_mail_template')
        # email_to =  self.company_id.receptionist_email 
        # if email_to:
        #     email_values = {"email_to": email_to}
        #     ctx = {"receptionist_email":email_to,
        #            "ctx": self.employee_meal_line}
        #     template_id.with_context(ctx).send_mail(self.id, email_values=email_values)
            
        self.write({'state': 'confirm'})
        
        
        
        
        
        
    def action_approve(self):
        self.write({'state': 'approved'})
        
    def action_cancel(self):
        self.write({'state': 'cancel'})
        
        
        
        
        
        
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.move') or _('New')
        return super().create(vals)

    # def unlink(self):
    #     if any(rec.state != 'draft' for rec in self):
    #         raise ValidationError(_("You only can delete draft meal!"))
    #     return super(HrMeal, self).unlink()
