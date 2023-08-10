# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _


class WizardHRSubcontract(models.TransientModel):
    _name = "wizard.hr.subcontract"
    _description = "Wizard Create HR Subcontract"

    def _get_domain_hr_responsible(self):
        domain = []
        contract_gr = self.env.ref('erpvn_hr_contract.group_hr_contract_user')
        if contract_gr:
            domain = [('id', 'in', contract_gr.users.ids)]
        return domain

    active = fields.Boolean(default=True)
    name = fields.Char('Contract Reference', required=True)
    is_trial = fields.Boolean("Is Trial?", default=False, copy=False)
    contract_id = fields.Many2one('hr.contract', 'Contract')
    structure_type_id = fields.Many2one('hr.payroll.structure.type', string="Salary Structure Type")
    employee_id = fields.Many2one('hr.employee', string='Employee', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    department_id = fields.Many2one('hr.department', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", string="Department")
    job_id = fields.Many2one('hr.job', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", string='Job Position')
    date_start = fields.Date('Start Date', required=True, help="Start date of the contract.")
    date_end = fields.Date('End Date', help="End date of the contract (if it's a fixed-term contract).")
    trial_date_end = fields.Date('End of Trial Period', help="End date of the trial period (if there is one).")
    resource_calendar_id = fields.Many2one('resource.calendar', 'Working Schedule')
    wage = fields.Monetary('Wage', required=True, help="Employee's monthly gross wage.")
    notes = fields.Text('Notes')
    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Running'),
        ('close', 'Expired'),
        ('cancel', 'Cancelled')
    ], string='Status', group_expand='_expand_states', copy=False,
       help='Status of the contract', default='draft')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    company_country_id = fields.Many2one('res.country', string="Company country", related='company_id.country_id', readonly=True)
    kanban_state = fields.Selection([
        ('normal', 'Grey'),
        ('done', 'Green'),
        ('blocked', 'Red')
    ], string='Kanban State', default='normal', copy=False)
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    permit_no = fields.Char('Work Permit No', related="employee_id.permit_no", readonly=False)
    visa_no = fields.Char('Visa No', related="employee_id.visa_no", readonly=False)
    visa_expire = fields.Date('Visa Expire Date', related="employee_id.visa_expire", readonly=False)
    hr_responsible_id = fields.Many2one('res.users', 'HR Responsible', help='Person responsible for validating the employee\'s contracts.', domain=_get_domain_hr_responsible)
    calendar_mismatch = fields.Boolean()
    first_contract_date = fields.Date(related='employee_id.first_contract_date')
    contract_time = fields.Selection([('past', 'Past'), ('current', 'Current'), ('future', 'Future')], string="Contract Time")
    contract_type_id = fields.Many2one('hr.contract.type', string="Contract Type", required=True)
    over_hour = fields.Monetary('Hour Wage')
    over_day = fields.Monetary('Day Wage')
    no_required_attendance = fields.Boolean(string='No Required Check Fingerprint?', default=False)
    notice_days = fields.Integer(string="Notice Period", default=30)
    wizard_allowance_ids = fields.One2many('wizard.hr.subcontract.allowance', 'wizard_subcontract_id', 'Allowance')
    job_title_id = fields.Many2one(string='Job Title', comodel_name='hr.job.title', ondelete='restrict',)
    option_create = fields.Selection(
        string='Select Subcontract',
        selection=[('salary', 'Salary'),('Job', 'Job Position'),('both', 'Salary & Job Position')], 
        default='salary'
        )
    

    @api.onchange('date_start', 'contract_type_id')
    def _onchange_date_start(self):
        for contract in self:
            update_vals = {}
            if contract.contract_type_id:
                update_vals.update({'is_trial': contract.contract_type_id.is_trial})
                if contract.date_start:
                    if contract.contract_type_id.range_days > 0.0:
                        date_end = contract.date_start
                        if contract.contract_type_id.range_type == 'days':
                            date_end += relativedelta(days=contract.contract_type_id.range_days)
                        else:
                            date_end += relativedelta(months=contract.contract_type_id.range_days)

                        update_vals.update({'date_end': date_end})
            if update_vals:
                contract.write(update_vals)

    def _prepare_contract_vals(self, contract):
        return {
            'active': contract.active,
            'is_trial': contract.is_trial,
            'structure_type_id': contract.structure_type_id.id,
            'employee_id': contract.employee_id.id,
            'department_id': contract.department_id.id,
            'job_id': contract.job_id.id,
            'job_title_id': contract.job_title_id.id,
            'trial_date_end': contract.trial_date_end,
            'wage': contract.wage,
            'notes': contract.notes,
            'company_id': contract.company_id.id,
            'hr_responsible_id': contract.hr_responsible_id.id,
            'contract_type_id': contract.contract_type_id.id,
            'over_hour': contract.over_hour,
            'over_day': contract.over_day,
            'notice_days': contract.notice_days,
            'struct_id': contract.struct_id.id,
            'schedule_pay': contract.schedule_pay,
            'remain_time_off': contract.remain_time_off,
            'analytic_account_id': contract.analytic_account_id.id,
            'no_required_attendance': contract.no_required_attendance,
        }

    def _prepare_updating_contract_vals(self, contract):
        res = self._prepare_contract_vals(contract)
        allowance_vals = [(5, 0, 0)] + [(0, 0, allowance._prepare_wizard_allowance_vals()) for allowance in contract.wizard_allowance_ids]
        res.update({'allowance_ids': allowance_vals})
        return res

    def _prepare_creating_subcontract_vals(self, contract):
        res = self._prepare_contract_vals(contract)
        allowance_vals = [(5, 0, 0)] + [(0, 0, allowance._prepare_allowance_vals()) for allowance in contract.allowance_ids]
        res.update({'allowance_ids': allowance_vals})
        return res


    def create_hr_subcontract(self):

        contract = self
        updating_contract_vals = self._prepare_updating_contract_vals(contract)
        if self.option_create == 'salary':
            # update the existed contract from wizard.
            updating_contract_vals.update({
                # 'date_start': contract.date_start,
                # 'date_end': contract.date_end,
                'resource_calendar_id':contract.resource_calendar_id.id,
                'wage':self.wage,
                'allowance_ids': [(5, 0, 0)] + [(0, 0, allowance._prepare_wizard_allowance_vals()) for allowance in self.wizard_allowance_ids]
            })

        if self.option_create == 'Job':
            # update the existed contract from wizard.
            updating_contract_vals.update({
                # 'date_start': contract.date_start,
                # 'date_end': contract.date_end,
                'resource_calendar_id':contract.resource_calendar_id.id,
                'job_id':self.job_id.id,
                'job_title_id': self.job_title_id.id,
            })

        if self.option_create == 'both':
            # update the existed contract from wizard.
            updating_contract_vals.update({
                # 'date_start': contract.date_start,
                # 'date_end': contract.date_end,
                'resource_calendar_id':contract.resource_calendar_id.id,
                'wage':self.wage,
                'allowance_ids': [(5, 0, 0)] + [(0, 0, allowance._prepare_wizard_allowance_vals()) for allowance in self.wizard_allowance_ids],
                'job_id':self.job_id.id,
                'job_title_id': self.job_title_id.id,
            })
        
        # # create a new subcontract
        subcontract_vals = self._prepare_creating_subcontract_vals(self.contract_id)
        subcontract_vals.update({
            'name': self.name,
            'state': 'close',
            'date_start': self.date_start,
            # 'date_end': fields.Date.today() if fields.Date.today() >= self.contract_id.date_start else self.contract_id.date_start,
            'date_end': self.contract_id.date_end,
            'contract_id': self.contract_id.id,
            'resource_calendar_id':self.contract_id.resource_calendar_id.id,
            'subcontract_info': self.option_create,
        })
        subcontract=self.env['hr.subcontract'].create(subcontract_vals)

        self.contract_id.write(updating_contract_vals)
        form_view_id= self.env.ref('erpvn_hr_contract.hr_subcontract_form_view', raise_if_not_found=False)
        return True

        # self.ensure_one()

        # # create a new subcontract
        # subcontract_vals = self._prepare_creating_subcontract_vals(self.contract_id)
        # subcontract_vals.update({
        #     'name': self.name,
        #     'state': 'close',
        #     'date_start': self.contract_id.date_start,
        #     'date_end': fields.Date.today() if fields.Date.today() >= self.contract_id.date_start else self.contract_id.date_start,
        #     'contract_id': self.contract_id.id,
        #     'resource_calendar_id':self.contract_id.resource_calendar_id.id

        # })
        # self.env['hr.subcontract'].create(subcontract_vals)

        # # update the existed contract from wizard.
        # contract = self
        # updating_contract_vals = self._prepare_updating_contract_vals(contract)
        # updating_contract_vals.update({
        #     'date_start': contract.date_start,
        #     'date_end': contract.date_end,
        #     'resource_calendar_id':contract.resource_calendar_id.id
        # })
        # self.contract_id.write(updating_contract_vals)
        # return True


class WizardHRSubcontractAllowance(models.TransientModel):
    _name = "wizard.hr.subcontract.allowance"
    _description = "Wizard HR Subcontract Allowance"

    wizard_subcontract_id = fields.Many2one('wizard.hr.subcontract', 'Wizard Contract')
    contract_id = fields.Many2one('hr.contract', 'Contract')
    code = fields.Char('Code')
    description = fields.Text('Description')
    amount = fields.Float('Amount')
    apply_on = fields.Selection([('monthly', 'Monthly'), ('daily', 'Daily'), ('hourly', 'Hourly')], string='Apply on', default='monthly')
    contract_type_id = fields.Many2one('hr.payroll.structure.type', 'Payroll Structure Type')

    def _prepare_wizard_allowance_vals(self):
        return {
            'code': self.code,
            'description': self.description,
            'amount': self.amount,
            'apply_on': self.apply_on,
            'contract_type_id': self.contract_type_id.id,
        }