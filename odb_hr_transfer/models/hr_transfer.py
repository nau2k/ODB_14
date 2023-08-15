# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Hrtransfer(models.Model):
    _name = "hr.transfer"
    _description = "HR transfer"
    _inherit = "mail.thread"

    name = fields.Char(string="Name")
    # state = fields.Selection(
    #     [
    #         ("draft", "Draft"),
    #         ("confirm", "Confirmed"),
    #         ("approved", "Approved"),
    #         ("cancel", "Cancelled"),
    #     ],  default="draft", index=True,copy=False, tracking=True, string="Status",   )
    company_id = fields.Many2one( "res.company", string="Company", default=lambda self: self.env.company)

    employee_id = fields.Many2one("hr.employee", string="Employee")
    barcode = fields.Char(related='employee_id.barcode')
    
    department_id = fields.Many2one( "hr.department", string="Department", )
    job_id = fields.Many2one("hr.job", string="Job Position", )
    title_id = fields.Many2one(string="Job Title", comodel_name="hr.job.title",)

    
    responsible_id = fields.Many2one( "res.users", string="Responsible")
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    
