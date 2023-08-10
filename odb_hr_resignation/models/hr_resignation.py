# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

date_format = "%Y-%m-%d"
RESIGNATION_TYPE = [
    ('resigned', 'Normal Resignation'),
    ('fired', 'Fired by the company')
]

class HrResignation(models.Model):
    _name = 'hr.resignation'
    _description = 'HR Resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id.id, help='Name of the employee for whom the request is creating')
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id', help='Department of the employee')
    company_id = fields.Many2one(comodel_name='res.company',string='Company', required=True, readonly=True,default=lambda self: self.env.company)
    resign_confirm_date = fields.Date(string="Confirmed Date", help='Date on which the request is confirmed by the employee.', tracking=True)
    approved_revealing_date = fields.Date(string="Approved Last Day Of Employee", help='Date on which the request is confirmed by the manager.', tracking=True)
    joined_date = fields.Date(string="Join Date", store=True, help='Joining date of the employee.i.e Start date of the first contract')
    # expected_revealing_date = fields.Date(string="Last Working Day",
    #     default=datetime.now() + relativedelta(days=30), required=True, help='Employee requested date on which he is revealing from the company.')
    expected_revealing_date = fields.Date(string="Last Working Day",
        default=datetime.now(), required=True, help='Employee requested date on which he is revealing from the company.')
    reason = fields.Text(string="Reason", help='Specify reason for leaving the company')
    # notice_period = fields.Char(string="Notice Period")
    notice_period = fields.Integer(string="Notice Period",default =0)
    # state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('approved', 'Approved'), ('cancel', 'Rejected')],
    #     string='Status', default='draft', tracking=True)
    state = fields.Selection([('draft', 'Draft'),("waiting", "Waiting"), ('confirm', 'Confirm'), ('approved', 'Approved'), ('cancel', 'Rejected')],
        string='Status', default='draft', tracking=True)
    resignation_type = fields.Selection(selection=RESIGNATION_TYPE, default='resigned' ,help="Select the type of resignation: normal resignation or fired by the company")
    # read_only = fields.Boolean(string="check field")
    employee_contract_id = fields.Many2one('hr.contract', string="Contract")
    is_manager = fields.Boolean(default= False)
    is_future_day = fields.Boolean(compute='_compute_is_future_day' )
    
    @api.model
    def default_get(self, fields):
        res = super(HrResignation, self).default_get(fields)
        if not self.env.user.employee_id:
            raise UserError(_(" Your account need to be connected to an employee to process."))
        if self.user_has_groups("hr.group_hr_user"):
            res['is_manager'] = True
        if len(self.env.user.employee_id.contract_ids)== 0 :
            raise UserError(_(" You don't have a contract !!"))
        return res
    
    
    

    
    @api.constrains('expected_revealing_date','approved_revealing_date','resign_confirm_date')
    def validate_time(self):
        for rec in self:
            if rec.approved_revealing_date and rec.resign_confirm_date:
                if rec.resign_confirm_date > rec.approved_revealing_date:
                    raise ValidationError(_('The Approved date must be greater than the Confirm date'))
                

        
    @api.depends('expected_revealing_date')
    def _compute_is_future_day(self):
        for rec in self:
            rec.is_future_day = False
            today = fields.Date.today() 
            if not self.user_has_groups("hr.group_hr_user"):
                resign_notice_period = fields.Date.today() + relativedelta(days=self.notice_period)
                if rec.expected_revealing_date < resign_notice_period:
                    raise UserError(_('The last working day is at least %s', resign_notice_period))
            if rec.expected_revealing_date >= today:
                    rec.is_future_day = True
            

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.employee_contract_id = False
        self.notice_period = False
        # self.expected_revealing_date  = False
    
    @api.onchange('expected_revealing_date')
    def _onchange_expected_revealing_date(self):
        self.resign_confirm_date = False
        self.approved_revealing_date = False
    

    @api.onchange('employee_id')
    def set_join_date(self):
        # self.joined_date = self.employee_id.joining_date if self.employee_id.joining_date else ''
        self.joined_date = self.employee_id.joining_date

    # @api.depends('employee_id')
    # def compute_join_date(self):
    #     # self.joined_date = self.employee_id.joining_date if self.employee_id.joining_date else ''
    #     if employee_id.joining_date :
    #         self.joined_date = self.employee_id.joining_date
    #     else :
    #         self.joined_date = False

    # def check_date(self,vals):
    #     if vals.get('state')=='draft':
    #         if vals.get('expected_revealing_date') < date.today().strftime(date_format):
    #             raise ValidationError (_("The last working day must not be less than the current day "))
    @api.model
    def create(self, vals):
        # assigning the sequence for the record
        # self.check_date(vals)
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')
        res = super(HrResignation, self).create(vals)
        return res

    @api.constrains('employee_id')
    def check_employee(self):
        # Checking whether the user is creating leave request of his/her own
        for rec in self:
            if not self.env.user.has_group('hr.group_hr_user'):
                if rec.employee_id.user_id.id and rec.employee_id.user_id.id != self.env.uid:
                    raise ValidationError(_('You cannot create request for other employees'))

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def check_request_existence(self):
        # Check whether any resignation request already exists
        for rec in self:
            if rec.employee_id:
                resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
                                                                         ('state', 'in', ['waiting','confirm', 'approved'])])
                if resignation_request:
                    raise ValidationError(_('There is a resignation request in confirmed or'
                                            ' approved state for this employee'))
                if rec.employee_id:
                    no_of_contract = self.env['hr.contract'].sudo().search([('employee_id', '=', self.employee_id.id)])
                    for contracts in no_of_contract:
                        if contracts.state == 'open':
                            rec.employee_contract_id = contracts
                            # rec.write({'employee_contract_id': contracts.id})
                            rec.notice_period = contracts.notice_days
                            rec.expected_revealing_date = fields.Date.today() + relativedelta(days=contracts.notice_days)
                            rec.joined_date = contracts.first_contract_date



    # @api.onchange('employee_id')
    # @api.depends('employee_id')
    # def check_request_existence(self):
    #     # Check whether any resignation request already exists
    #     for rec in self:
    #         if rec.employee_id:
    #             resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
    #                                                                      ('state', 'in', ['confirm', 'approved'])])
    #             if resignation_request:
    #                 raise ValidationError(_('There is a resignation request in confirmed or'
    #                                         ' approved state for this employee'))
    #             if rec.employee_id:
    #                 no_of_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
    #                 for contracts in no_of_contract:
    #                     if contracts.state == 'open':
    #                         rec.employee_contract_id = contracts
    #                         # rec.write({'employee_contract_id': contracts.id})
    #                         rec.notice_period = contracts.notice_days
    #                         rec.joined_date = contracts.first_contract_date

    @api.constrains('joined_date')
    def _check_dates(self):
        # validating the entered dates
        for rec in self:
            resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
                                                                     ('state', 'in', ['confirm', 'approved'])])
            if resignation_request:
                raise ValidationError(_('There is a resignation request in confirmed or'
                                        ' approved state for this employee'))

    def send_resignation(self):
        if not self.joined_date:
            raise ValidationError(_('Please set joining date for the employee'))
        if self.joined_date >= self.expected_revealing_date:
            raise ValidationError(_('Last date of the employee must be before the joining date'))
        
        # send email state 'waiting '
        temlate_email_waiting = self.env.ref('odb_hr_resignation.waiting_resgin_request')
        temlate_email_waiting.send_mail(self.id, force_send=True)
        self.write({'state': 'waiting'})


    def confirm_resignation(self):
        if self.resign_confirm_date:
            self.state = 'confirm'
            
        else:
            view = self.env.ref("odb_hr_resignation.wz_resign_confirm")
            wiz = self.env["wz.resign.confirm"].create(
                {
                    "resign_confirm_ids": [(4, self.id)],
                    "resign_confirm_date": self.resign_confirm_date,
                    "expected_revealing_date": self.expected_revealing_date,
                }
            )
            return {
                "name": _("Warning?"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "wz.resign.confirm",
                "views": [(view.id, "form")],
                "view_id": view.id,
                "target": "new",
                "res_id": wiz.id,
                "context": self.env.context,
            }
    def _confirm_resignation(self,confirm_date):
        if confirm_date:
            self.resign_confirm_date = confirm_date
            self.confirm_resignation()

    def cancel_resignation(self):
        temlate_email_cancel = 'odb_hr_resignation.cancel_resgin_request'
        email_to = self.employee_id.parent_id.work_email
        self.send_email_cus(temlate_email_cancel,email_to)
        self.write({'state': 'cancel'})
        return True
        


    def reject_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    def reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.employee_id.active = True
            rec.employee_id.resigned = False
            rec.employee_id.fired = False
            rec.resign_confirm_date = False
            rec.approved_revealing_date = False
            
        



    def approve_resignation(self):
        if self.approved_revealing_date:
            for rec in self:
                if rec.expected_revealing_date and rec.resign_confirm_date:
                    no_of_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
                    for contracts in no_of_contract:
                        if contracts.state == 'open':
                            rec.employee_contract_id = contracts
                            rec.state = 'approved'
                            # rec.approved_revealing_date = rec.resign_confirm_date + timedelta(days=contracts.notice_days)
                            contracts.with_context(skip_update_expected_date=True).write({
                                'date_end': rec.expected_revealing_date,
                                'view_expected_end': True,
                                'state': 'close',
                            })
                            contracts.mapped('subcontract_ids').with_context(skip_update_expected_date=True)\
                                .write({'date_end': rec.expected_revealing_date, 'view_expected_end': True})
                        # else:
                        #     rec.approved_revealing_date = rec.expected_revealing_date
                        
                    # Changing state of the employee if resigning today
                    if rec.expected_revealing_date <= fields.Date.today() and rec.employee_id.active:
                        rec.employee_id.active = False
                        # Changing fields in the employee table with respect to resignation
                        rec.employee_id.resign_date = rec.expected_revealing_date
                        if rec.resignation_type == 'resigned':
                            rec.employee_id.resigned = True
                        else:
                            rec.employee_id.fired = True
                        # Removing and deactivating user
                        if rec.employee_id.user_id:
                            rec.employee_id.user_id.active = False
                            rec.employee_id.user_id = None
                else:
                    raise ValidationError(_('Please enter valid dates.'))

        else:
            view = self.env.ref("odb_hr_resignation.wz_resign_approved")
            wiz = self.env["wz.resign.approved"].create(
                {
                    "resign_confirm_ids": [(4, self.id)],
                    "resign_confirm_date": self.resign_confirm_date,
                    "expected_revealing_date": self.expected_revealing_date,
                }
            )
            return {
                "name": _("Warning?"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "wz.resign.approved",
                "views": [(view.id, "form")],
                "view_id": view.id,
                "target": "new",
                "res_id": wiz.id,
                "context": self.env.context,
            }
    def _approve_resignation(self,approved_date):
        if approved_date:
            self.approved_revealing_date = approved_date
            self.approve_resignation()
                
                
    # def approve_resignation(self):
    #     for rec in self:
    #         if rec.expected_revealing_date and rec.resign_confirm_date:
    #             no_of_contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
    #             for contracts in no_of_contract:
    #                 if contracts.state == 'open':
    #                     rec.employee_contract_id = contracts
    #                     rec.state = 'approved'
    #                     rec.approved_revealing_date = rec.resign_confirm_date + timedelta(days=contracts.notice_days)
    #                     contracts.with_context(skip_update_expected_date=True).write({
    #                         'date_end': rec.expected_revealing_date,
    #                         'view_expected_end': True,
    #                         'state': 'close',
    #                     })
    #                     contracts.mapped('subcontract_ids').with_context(skip_update_expected_date=True)\
    #                         .write({'date_end': rec.expected_revealing_date, 'view_expected_end': True})
    #                 else:
    #                     rec.approved_revealing_date = rec.expected_revealing_date
    #             # Changing state of the employee if resigning today
    #             if rec.expected_revealing_date <= fields.Date.today() and rec.employee_id.active:
    #                 rec.employee_id.active = False
    #                 # Changing fields in the employee table with respect to resignation
    #                 rec.employee_id.resign_date = rec.expected_revealing_date
    #                 if rec.resignation_type == 'resigned':
    #                     rec.employee_id.resigned = True
    #                 else:
    #                     rec.employee_id.fired = True
    #                 # Removing and deactivating user
    #                 if rec.employee_id.user_id:
    #                     rec.employee_id.user_id.active = False
    #                     rec.employee_id.user_id = None
    #         else:
    #             raise ValidationError(_('Please enter valid dates.'))

    def update_employee_status(self):
        resignation = self.env['hr.resignation'].search([('state', '=', 'approved')])
        for rec in resignation:
            if rec.expected_revealing_date <= fields.Date.today() and rec.employee_id.active:
                rec.employee_id.active = False
                # Changing fields in the employee table with respect to resignation
                rec.employee_id.resign_date = rec.expected_revealing_date
                if rec.resignation_type == 'resigned':
                    rec.employee_id.resigned = True
                else:
                    rec.employee_id.fired = True
                # Removing and deactivating user
                if rec.employee_id.user_id:
                    rec.employee_id.user_id.active = False
                    rec.employee_id.user_id = None

    def action_py3o_print(self):
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/binary/download_resignation?model=hr.payslip&field=data&id=%s'%(self.ids),
            'target': 'self',
        }

    
    def send_email_cus(self,template,email_to):
        mail_server = self.env["ir.mail_server"].sudo().search([('active','=',True)], order='sequence asc', limit=1 )
        if not mail_server:
            return 
        temlate_email = self.env.ref(template)
        if email_to:
            email_value = {
                "email_to": email_to,  
                "email_from": mail_server.smtp_user,
            }
            temlate_email.sudo().send_mail(
                self.id, force_send=True, email_values=email_value)

    def unlink(self):
        if any(rec.state !='draft' for rec in self):
            raise UserError(_('You cannot delete a resigntion which is not draft!'))
        return super(HrResignation, self).unlink()
    