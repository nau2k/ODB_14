# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id')

class HrEmployeePrivate(models.Model):
    _inherit='hr.employee'

    barcode = fields.Char(groups="base.group_user")
    personal_mobile = fields.Char(string='Mobile', related='address_home_id.mobile', store=True,
        help="Personal mobile number of the employee")
    joining_date = fields.Date(string='Joining Date', help="Employee joining date computed from the contract start date")
    id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(string='Passport Expiry Date', help='Expiry date of Passport ID')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
        string="Attachment", help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1',
        string="Passport Attachment", help='You can attach the copy of Passport')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information')
    resign_date = fields.Date('Resign Date', readonly=True, help="Date of the resignation")
    resigned = fields.Boolean(string="Resigned", default=False, store=True,help="If checked then employee has resigned")
    fired = fields.Boolean(string="Fired", default=False, store=True, help="If checked then employee has fired")
    children = fields.Integer(string='Number of Children', groups="hr.group_hr_user", store=True, tracking=True, compute="_compute_number_of_children")
    permit_from = fields.Date('Permit Date From', groups="hr.group_hr_user", tracking=True)
    permit_to = fields.Date('Permit Date To', groups="hr.group_hr_user", tracking=True)
    identification_id = fields.Char(required=True)
    identification_created_date = fields.Date('Identification Created On', groups="hr.group_hr_user", help="Date created ID", tracking=True)
    identification_created_place = fields.Char('Identification Created At', groups="hr.group_hr_user", help="Place created ID", tracking=True)
    identification_address = fields.Char('Identification Address', groups="hr.group_hr_user", help="Address ID", tracking=True)
    place_of_permanent = fields.Char('Place of permanent', groups="hr.group_hr_user", help="The adress where created ID", tracking=True)
    ethnic = fields.Char('Ethnic', groups="hr.group_hr_user", tracking=True)
    religion = fields.Char('Religion', groups="hr.group_hr_user", tracking=True)
    age = fields.Integer(compute="_compute_age")
    birthday = fields.Date('Date of Birth', groups="base.group_user", help="Birthday")
    res_partner_ids = fields.One2many('res.partner', 'employee_id', string='Contacts')
    title_id = fields.Many2one(string='HR Job Title', comodel_name='hr.job.title', ondelete='restrict',)
    employee_type_id = fields.Many2one('hr.employee.type', string="Employee Type")
    job_id = fields.Many2one('hr.job', store=True,readonly=False, compute='_compute_job')

    allocation_total_display = fields.Char(compute='_compute_allocation_display')
    allocation_remained_display = fields.Char(compute='_compute_allocation_display')
    allocation_taken_display = fields.Char(compute='_compute_allocation_display')

    allocation_total = fields.Float(compute='_compute_allocation_display')
    allocation_remained = fields.Float(compute='_compute_allocation_display')
    allocation_taken = fields.Float(compute='_compute_allocation_display')

    seniority_leave = fields.Integer(string='Seniority Leave', store=True)

    working_history_ids = fields.One2many('working.hour.history', 'employee_id', string='Working Hours History')

    @api.constrains('work_email')
    def _check_work_email(self):
        for rec in self:
            if rec.work_email:
                employee_id = self.sudo().env['hr.employee'].search([('id', '!=', rec.id), ('work_email', '=', rec.work_email)], limit=1)
                if employee_id:
                    raise ValidationError(_(
                        "The work email %(work_email)s has been set for employee %(employee_name)s.",
                        work_email=rec.work_email,
                        employee_name=employee_id.mapped('display_name'),
                    ))

    def _compute_allocation_display(self):
        for employee in self:
            annual_leave_id = self.env['hr.leave.type'].sudo().search([('code', '=', 'ANPL')], limit=1)
            data_days = annual_leave_id.get_employees_days([employee.id])[employee.id]
            result = data_days.get(annual_leave_id.id, {})

            total = result.get('max_leaves', 0)
            taken = result.get('max_leaves', 0) - result.get('virtual_remaining_leaves', 0)
            remain = result.get('virtual_remaining_leaves', 0) if result.get('virtual_remaining_leaves', 0) > 0 else 0

            employee.allocation_total = round(total, 2)
            employee.allocation_taken = round(taken, 2)
            employee.allocation_remained = round(remain, 2)

            employee.allocation_total_display = '%s:%s (hours)' % (int(total), round((total % 1) * 60))
            employee.allocation_taken_display = '%s:%s (hours)' % (int(taken), round((taken % 1) * 60))
            employee.allocation_remained_display = '%s:%s (hours)' % (int(remain), round((remain % 1) * 60))

    @api.model
    def create(self, vals):
        record = super(HrEmployeePrivate, self).create(vals)
        # update value from hr.employee for resource.resource
        record.resource_id.write({
            'department_id': record.department_id.id,
            'employee_id': record.id
        })
        #create first record in employee
        self.create_first_history_working(record)
        return record
        
    def write(self, vals):
        if self.env.context.get("no_update_resource_calendar") != True:
            res = super(HrEmployeePrivate, self).write(vals)
            # update value from hr.employee for resource.resource
            for record in self:
                record.resource_id.write({
                    'department_id': record.department_id.id,
                    'employee_id': record.id
                })
            #create record history working hours in employee
            if 'resource_calendar_id' in vals:
                self.history_working_hours()
            return res

    @api.onchange('job_id', 'department_id')
    def _onchange_job(self):
        for record in self:
            if record.job_id and record.title_id.id not in record.job_id.title_ids.ids or not record.job_id:
                record.title_id = False

    @api.onchange('job_id', 'department_id')
    def _get_domain_title(self):
        self.ensure_one()
        title_id_list = []
        if self.department_id:
            title_id_list += self.department_id.jobs_ids.ids + self.department_id.child_ids.jobs_ids.ids
        if self.job_id:
            title_id_list = self.job_id.title_ids.ids
        return {'domain': {'title_id': [('id', 'in', title_id_list)]}}

    @api.onchange('department_id')
    def _onchange_section(self):
        for record in self:
            if record.department_id:
                if (record.job_id.id not in record.department_id.jobs_ids.ids +  record.department_id.child_ids.jobs_ids.ids):
                    record.job_id = False

    @api.onchange('department_id')
    def _get_domain_job(self):
        self.ensure_one()
        job_id_list = []
        if self.department_id:
            job_id_list += self.department_id.jobs_ids.ids + self.department_id.child_ids.jobs_ids.ids
        job_id_list = list(set(job_id_list))
        return {'domain': {'job_id': [('id', 'in', job_id_list)]}}

    @api.depends("birthday")
    def _compute_age(self):
        for record in self:
            age = 0
            if record.birthday:
                age = relativedelta(fields.Date.today(), record.birthday).years
            record.age = age

    @api.depends('fam_ids')
    def _compute_number_of_children(self):
        for employee in self:
            employee.children = len(employee.fam_ids.filtered(lambda x: x.relation_id.is_children))

    #announcement management
    def _announcement_count(self):
        now = datetime.now()
        now_date = now.date()
        announce_obj = self.env['hr.announcement'].sudo()

        for employee in self:
            employee.announcement_count = announce_obj.search_count([
                ('date_start', '<=', now_date), 
                ('state', 'in', ['approved', 'done']), 
                ('is_announcement', '=', True),
                '|', '|', 
                ('employee_ids', 'in', employee.ids), 
                ('department_ids', 'in', employee.department_id.ids), 
                ('position_ids', 'in', employee.job_id.ids)
            ])

    def announcement_view(self):
        now = datetime.now()
        now_date = now.date()
        announce_obj = self.env['hr.announcement'].sudo()

        for employee in self:

            ann_ids = announce_obj.search([
                ('date_start', '<=', now_date), 
                ('state', 'in', ['approved', 'done']), 
                ('is_announcement', '=', True),
                '|', '|', 
                ('employee_ids', 'in', employee.ids), 
                ('department_ids', 'in', employee.department_id.ids), 
                ('position_ids', 'in', employee.job_id.ids)
            ]).ids
            
            view_id = self.env.ref('hr_reward_warning.view_hr_announcement_form').id
            if ann_ids:
                if len(ann_ids) > 1:
                    value = {
                        'domain': str([('id', 'in', ann_ids)]),
                        'view_mode': 'tree,form',
                        'res_model': 'hr.announcement',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Announcements'),
                        'res_id': ann_ids
                    }
                else:
                    value = {
                        'view_mode': 'form',
                        'res_model': 'hr.announcement',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Announcements'),
                        'res_id': ann_ids and ann_ids[0]
                    }
                return value

    announcement_count = fields.Integer(compute='_announcement_count', string='# Announcements', help="Count of Announcement's")

    def action_create_user(self):
        self.ensure_one()
        self.env['res.users'].create(dict(
            login=self.work_email,
            company_id=self.env.company.id,
            
        ))

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """  Find Customer names according to its bacode, name, mobile phone, work email"""
        if name and not self.env.context.get('import_file'):
            args = args or []
            args.extend([
                '|', ['barcode', 'ilike', name],
                '|', ['name', 'ilike', name],
                '|', ['mobile_phone', 'ilike', name],
                 ['work_email', 'ilike', name],
                #  ['work_phone', 'ilike', name],
                # ['function', 'ilike', name]
            ])
            name = ''
        return super(HrEmployeePrivate, self).name_search(
            name=name, args=args, operator=operator, limit=limit)

    def mail_reminder(self):
        """Sending expiry date notification for ID and Passport"""

        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                if date_now >= exp_date1:
                    mail_content = "  Hello  " + i.name + ",<br>Your Passport " + i.passport_id + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    @api.model
    def _default_employee_code(self):
        return self.env['ir.sequence'].next_by_code('employee.code')

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)

    def action_make_contact(self):
        self.ensure_one()

        contact_vals = {
            'name': self.name.capitalize() if self.name else '',
            'employee_id': self.id,
            'employee': True,
            'is_internal': True,
            'type': 'contact',
            'company_type': 'person',
            'function': self.job_title,
            'lang': self.env.user.lang or 'en_US',
        }

        if self.company_id:
            contact_vals.update({
                'company_id': self.company_id.id,
                'parent_id': self.company_id.id,
                'website': self.company_id.website or '',
            })

        # get phone info.
        if self.mobile_phone:
            contact_vals.update({'phone': self.mobile_phone})
        # get email info.
        if self.mobile_phone:
            contact_vals.update({'email': self.work_email})

        title_id =  self.env.ref('base.res_partner_title_miss')
        if self.gender == 'male':
            title_id =  self.env.ref('base.res_partner_title_miss')
        contact_vals.update({'title': title_id.id})

        # get address from company.
        address_fields = self._address_fields()
        if self.company_id.partner_id:
            partner_id = self.company_id.partner_id
            if any(partner_id[key] for key in address_fields):
                def convert(value):
                    return value.id if isinstance(value, models.BaseModel) else value
                contact_vals.update({key: convert(partner_id[key]) for key in address_fields})

        new_wizard = self.env['wizard.make.contact'].create(contact_vals)
        wz_form = self.env.ref('erpvn_hr_management.wizard_make_contact_form_view')
        if wz_form:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'wizard.make.contact',
                'target': 'new',
                'res_id': new_wizard.id,
                'views': [[wz_form.id, 'form']],
            }


    @api.model
    def generate_first_history_working(self):
        list_record = self.env['hr.employee'].sudo().search([('working_history_ids','=', False)])
        for record in list_record:
            record.create_first_history_working(record)

    def create_first_history_working(self,employee):
        emp = self.env['working.hour.history'].search([('is_first','=',True),('employee_id','=',employee.id)], limit=1)
        if not emp:
            self.env['working.hour.history'].sudo().create({
                'resource_calendar_id': employee.resource_calendar_id.id,
                'from_date': datetime.now().date(),
                'responsible_id': self.env.user.id if self.env.user.id else 1,
                'employee_id': employee.id,
                'is_first': True
            })
     
   
    def history_working_hours(self):
        emp = self.env['working.hour.history'].search([('to_date','=',False),('employee_id','=',self.id)])
        if emp:
            for rec in emp:
                rec.write({'to_date': datetime.now().date()})
        self.env['working.hour.history'].sudo().create({
            'resource_calendar_id': self.resource_calendar_id.id,
            'from_date': datetime.now().date(),
            'responsible_id': self.env.user.id if self.env.user.id else 1,
            'employee_id': self.id,
        })







# class HrEmployeeBaseInherit(models.AbstractModel):
#     _inherit = "hr.employee.base"

    # hr_presence_state = fields.Selection(store=True)