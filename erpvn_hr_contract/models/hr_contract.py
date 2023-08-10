# -*- coding: utf-8 -*-
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def _compute_domain_hr_responsible(self):
        # Nên xử lý bằng cách self.env.user.has_group('group_name')
        domain = []
        contract_gr = self.env['res.groups'].sudo().search([('name','=','group_hr_contract_user')])
#        contract_gr = self.env.ref('erpvn_hr_contract.group_hr_contract_user')
        if contract_gr:
            domain = [('id', 'in', contract_gr.users.ids)]
        return domain

    def _compute_contract_time(self):
        """@return past/current/future by compare today with the contract duration"""
        today = fields.Date.context_today(self)
        contracts = self.env['hr.contract'].search([])
        for contract in contracts:
            if contract.date_end and contract.date_end < today:
                contract.contract_time = 'past'
            elif (contract.date_end and contract.date_end > today) or (not contract.date_end and contract.date_start < today):
                contract.contract_time = 'current'
            elif contract.date_start > today:
                contract.contract_time = 'future'

    name = fields.Char(default=_("New"))
    hr_responsible_id = fields.Many2one(domain=_compute_domain_hr_responsible)
    is_trial = fields.Boolean("Is Trial?", default=False, copy=False)
    is_hardwork = fields.Boolean("Is Hard Work?", default=False, copy=False)
    contract_time = fields.Selection([('past', 'Past'), ('current', 'Current'), ('future', 'Future')],
        string="Contract Time", compute=_compute_contract_time, store=True)
    allowance_ids = fields.One2many('hr.contract.allowance', 'contract_id', 'Allowance')
    contract_type_id = fields.Many2one('hr.contract.type', string="Contract Type", required=True, tracking=True)
    sub_contract_id = fields.Many2one('hr.subcontract', string="Sub-Contract", readonly=True)
    # overtime.
    over_hour = fields.Monetary('Hour Wage')
    over_day = fields.Monetary('Day Wage')
    subcontract_ids = fields.One2many('hr.subcontract', 'contract_id', string='Subcontracts')
    no_required_attendance = fields.Boolean(string='No Required Check Fingerprint?', default=False)
    job_title_id = fields.Many2one(string='Job Title', comodel_name='hr.job.title', ondelete='restrict',)
    view_expected_end = fields.Boolean('View Expected End Field')
    expected_end = fields.Date(string='Expected End',)
    state = fields.Selection(selection_add=[
        ('draft', 'New'),
        ('open', 'Running'),
        ('expiring', 'Expiring'),
        ('termination', 'Termination'),
        ('close', 'Closed'),
        ('cancel', 'Cancelled')
    ],)

  

    @api.depends('employee_id')
    def _compute_employee_contract(self):
        super(HrContract, self)._compute_employee_contract()
        for contract in self.filtered('employee_id'):
            contract.job_title_id = contract.employee_id.title_id
            contract.department_id = contract.employee_id.department_id
            
    @api.onchange('department_id')
    def _onchange_department(self):
        for contract in self.filtered('employee_id'):
            if contract.job_title_id.department_id != contract.department_id:
                contract.job_title_id.department_id = contract.department_id

            if contract.job_id.department_id != contract.department_id:
                contract.job_id = contract.department_id.jobs_ids[0] if contract.department_id.jobs_ids else False
                
    # Kiem tra khi cap nhat lai contract 
    def check_state(self):
        for record in self:
            if record.state == 'open' and record.date_start and record.date_end:
                if record.date_end <= date.today():
                    record.write({'state': 'close'})

    def write(self, vals):
        super().write(vals)
        if 'date_end' in vals and not self._context.get('skip_update_expected_date', False):
            self.write({'expected_end': self.date_end})
        if self._name != 'hr.subcontract':
            self.check_state()
        return True

    def _add_allocations(self):
        self.ensure_one()
        self = self.sudo()
        if not self.contract_type_id.is_trial: # not a trial contract
            domain = [
                ('id', '!=', self.id),
                ('contract_type_id.is_trial', '=', True),
                ('employee_id', '=', self.employee_id.id),
                ('state', 'in', ['close', 'expiring']),
                ('date_end', '<=', self.date_start),
            ]
            holiday_status_id = self.env['hr.leave.type'].sudo().search([('code', '=', 'ANPL')], limit=1)
            # if not holiday_status_id:
                # holiday_status_id = self.env['hr.leave.mode.type'].sudo().search([('code', '=', 'Paid')], limit=1).type_ids[0]

            allocation_days = 1 if self.date_start.day <= 15 else 0
            add_allocation = False # flag to mark should create allocation or not.

            trial_contracts_str = ""
            # the trial contracts must be ended recently.
            for trial in self.search(domain).filtered(lambda x: (self.date_start - x.date_start).days < 130):
                if not add_allocation:
                    add_allocation = True

                trial_contracts_str += trial.name if trial_contracts_str == "" else ", " + trial.name
                if (trial.contract_type_id.range_type == 'days' and trial.contract_type_id.num_of_range == 30) \
                    or (trial.contract_type_id.range_type == 'months' and trial.contract_type_id.num_of_range == 1):
                    allocation_days += 1
                elif (trial.contract_type_id.range_type == 'days' and trial.contract_type_id.num_of_range == 60) \
                    or (trial.contract_type_id.range_type == 'months' and trial.contract_type_id.num_of_range == 2):
                    allocation_days += 2

            holiday = self.env['hr.leave.allocation'].search([('allocation_type', '=', 'accrual'), ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'validate'), ('holiday_type', '=', 'employee')], limit=1)

            if holiday:
                if holiday.accrual_limit > 0:
                    holiday.number_of_days = min(holiday.number_of_days + allocation_days, holiday.accrual_limit)
                    holiday.notes += _('Add %s day from the trial contract(s) "%s".') \
                        % (str(allocation_days), trial_contracts_str)
            # else:
            #     self.env['hr.leave.allocation'].with_user(SUPERUSER_ID).create({
            #         'name': 'Allocations leave monthly',
            #         'number_per_interval': 8.0,
            #         'unit_per_interval': 'hours',
            #         'allocation_type': 'accrual',
            #         'holiday_type': 'employee',
            #         'interval_unit': 'months',
            #         'interval_number': 1,
            #         'employee_id': self.employee_id.id,
            #         'state': 'validate',
            #         'holiday_status_id': holiday_status_id.id,
            #         'number_of_days': allocation_days,
            #         'nextcall': fields.Date.today() + relativedelta(months=1),
            #         'notes': _('Create the contract "%s": Add %s day from the trial contract(s) "%s".') \
            #             % (str(self.name), str(allocation_days), trial_contracts_str),
            #     })
        
    @api.model
    def create(self, vals):
        contract_name = vals.get('name', '')
        if vals.get('name', _('New')) == _('New'):
            employee = self.env['hr.employee'].browse(vals.get('employee_id', False))
            prefix = 'LBC-'
            if self.env['hr.contract.type'].browse(vals.get('contract_type_id')).is_trial:
                prefix = 'PAC-'

            contract_name = prefix + datetime.strptime(vals.get('date_start'), '%Y-%m-%d').date().strftime("%d%m%y") +'/' + str(employee.barcode)
            
        if self.env['hr.contract'].search_count([('name', '=', contract_name)]) > 0:
            raise ValidationError(_("Contract reference %s already exists, please check again") % (contract_name))

        if 'employee_id' not in vals:
            raise ValidationError(_("Employee is required."))
        
        vals['name'] = contract_name
        contract = super().create(vals)
        if contract.state == 'open':
            contract._add_allocations()
        return contract

    def action_run(self):
        # kiem tra nhan vien co bao nhieu hop dong va co hop dong nao dang con hieu luc khong
        # neu ton tai hop dong dang con hieu luc thi khong duoc approve hop dong moi
        contracts_to_run = self.filtered(lambda c: c.state == 'draft')
        if contracts_to_run:
            not_in = contracts_to_run.ids
            emp_not_in = contracts_to_run.employee_id.ids
            if self.env['hr.contract'].search([ ('employee_id', 'in', emp_not_in),('id', 'not in', not_in),('state','=','open')]):
                raise ValidationError(_('Employee %s has an unexpired contract \n')%([emp.employee_id.name for emp in contracts_to_run]))
            else:
                contracts_to_run.write({'state': 'open'})
                for contract in contracts_to_run:
                    contract._add_allocations()
            return True
        return False

    def action_set_draft(self):
        contracts_to_set_draft = self.filtered(lambda c: c.state == 'cancel')
        if contracts_to_set_draft:
            contracts_to_set_draft.write({'state': 'draft'})
            return True
        return False

    def action_cancel(self):
        contracts_to_cancel = self.filtered(lambda c: c.state != 'cancel')
        if contracts_to_cancel:
            contracts_to_cancel.write({'state': 'cancel'})
            return True
        return False

    def action_close(self):
        contracts_to_close = self.filtered(lambda c: c.state == 'open')
        if contracts_to_close:
            contracts_to_close.write({'state': 'close'})
            return True
        return False

    @api.onchange('date_start', 'contract_type_id')
    def _onchange_date_start(self):
        for contract in self:
            update_vals = {}
            if contract.contract_type_id:
                update_vals.update({'is_trial': contract.contract_type_id.is_trial})
                if contract.date_start:
                    date_end = False
                    if contract.contract_type_id.range_days > 0.0:
                        date_end = contract.date_start
                        if contract.contract_type_id.range_type == 'days':
                            date_end += relativedelta(days=contract.contract_type_id.range_days)
                        else:
                            date_end += relativedelta(months=contract.contract_type_id.range_days) - relativedelta(days=1)

                    update_vals.update({'date_end': date_end})

            if update_vals:
                contract.write(update_vals)

    @api.onchange('structure_type_id')
    def _onchange_structure_type_id(self):
        super(HrContract, self)._onchange_structure_type_id()
        for allowance in self.structure_type_id.allowance_ids:
            new_allowance = self.allowance_ids.new({
                'rule_id': allowance.rule_id and allowance.rule_id or False,
                'code': allowance.code,
                'description': allowance.description,
                'amount': allowance.amount,
                'apply_on': allowance.apply_on,
            })
            self.allowance_ids |= new_allowance

    @api.constrains('date_start', 'date_end', 'employee_id')
    def _check_date(self):
        if self._name != 'hr.subcontract':
            for record in self:
                employee_id = record.employee_id.id
                # previous contracts without date end
                contracts_no_date_end = self.search([('date_start', '<=', record.date_start), ('date_end', '=', False),
                    ('state', '=', 'open'), ('employee_id', '=', employee_id), ('id', '!=', record.id)])
                if contracts_no_date_end:
                    raise ValidationError(_("The previous contract (ID: %s, %s) must be ended before creating a new contract." % 
                        (contracts_no_date_end[0].id, contracts_no_date_end[0].name)))
                if record.date_end:
                    contracts = self.search([('date_start', '<=', record.date_end), ('state', '=', 'open'),
                        ('date_end', '>=', record.date_start), ('employee_id', '=', employee_id), ('id', '!=', record.id)])
                elif not record.date_end:
                    contracts = self.search([('date_end', '>=', record.date_start), ('state', '=', 'open'),
                        ('employee_id', '=', employee_id), ('id', '!=', record.id)])
                if contracts:
                    raise ValidationError(_("You cannot have 2 contracts of an employee overlapped on the same duration."))

    def unlink(self):
        not_draft_contract = self.filtered(lambda obj: obj.state != 'draft')
        if not_draft_contract:
            raise ValidationError(_("You only can delete draft contract!"))
        try:
            return super(HrContract, self).unlink()
        except BaseException:
            raise ValidationError(_("This contract is being used. You cannnot delete it."))

    def _assign_open_contract(self):
        if self._name != 'hr.subcontract':
            super(HrContract, self)._assign_open_contract()
    
    def _prepare_wizard_subcontract_vals(self):
        return {
            'active': self.active,
            'is_trial': self.is_trial,
            'structure_type_id': self.structure_type_id.id,
            'employee_id': self.employee_id.id,
            'department_id': self.department_id.id,
            'job_id': self.job_id.id,
            'job_title_id': self.job_title_id.id,
            'date_start': self.date_start, 
            'date_end': self.date_end,
            'trial_date_end': self.trial_date_end,
            'wage': self.wage,
            'notes': self.notes,
            'company_id': self.company_id.id,
            'hr_responsible_id': self.hr_responsible_id.id,
            'contract_type_id': self.contract_type_id.id,
            'over_hour': self.over_hour,
            'over_day': self.over_day,
            'no_required_attendance': self.no_required_attendance,
            'notice_days': self.notice_days,
            'contract_time': self.contract_time,
        }

    def action_create_subcontract(self):
        self.ensure_one()
        form_view_id = self.env.ref('erpvn_hr_contract.wizard_hr_subcontract_form_view', raise_if_not_found=False)
        wz_subcontract_val = self._prepare_wizard_subcontract_vals()

        wz_subcontract_val.update({
            'name': 'ADN-' + fields.Date.today().strftime("%d%m%y") + '/' + str(self.employee_id.barcode) + '-' + str(len(self.subcontract_ids) + 1),
            'wizard_allowance_ids': [(0, 0, allowance._prepare_allowance_vals()) for allowance in self.allowance_ids],
            'contract_id': self.id,
            'resource_calendar_id': self.resource_calendar_id.id,
        })

        wizard_id = self.env['wizard.hr.subcontract'].create(wz_subcontract_val)
        
        return {
            'name': _('Create Subcontract'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.hr.subcontract',
            'views': [(form_view_id.id, 'form')],
            'view_id': form_view_id.id,
            'target': 'new',
            'res_id': wizard_id.id,
        }


    def action_create_contract(self):
        self.ensure_one()
        form_view_id = self.env.ref('erpvn_hr_contract.wizard_hr_contract_form_view', raise_if_not_found=False)
        wz_contract_val = self._prepare_wizard_subcontract_vals()

        wz_contract_val.update({
            'name': 'New',
            'wizard_allowance_ids': [(0, 0, allowance._prepare_allowance_vals()) for allowance in self.allowance_ids],
            'contract_id': self.id,
            'resource_calendar_id': self.resource_calendar_id.id,
        })

        wizard_id = self.env['wizard.hr.subcontract'].create(wz_contract_val)
        
        return {
            'name': _('Make data current Contract'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.hr.subcontract',
            'views': [(form_view_id.id, 'form')],
            'view_id': form_view_id.id,
            'target': 'new',
            'res_id': wizard_id.id,
        }

    @api.constrains('employee_id', 'state', 'kanban_state', 'date_start', 'date_end')
    def _check_current_contract(self):
        """ Two contracts in state [incoming | open | close] cannot overlap """
        for contract in self.filtered(lambda c: (c.state not in ['draft', 'cancel'] or c.state == 'draft' and c.kanban_state == 'done') and c.employee_id):
            domain = [
                ('id', '!=', contract.id),
                ('employee_id', '=', contract.employee_id.id),
                '|',
                    ('state', '=', 'open'),
                    '&',
                        ('state', '=', 'draft'),
                        ('kanban_state', '=', 'done') # replaces incoming
            ]

            if not contract.date_end:
                start_domain = []
                end_domain = ['|', ('date_end', '>=', contract.date_start), ('date_end', '=', False)]
            else:
                start_domain = [('date_start', '<=', contract.date_end)]
                end_domain = ['|', ('date_end', '>', contract.date_start), ('date_end', '=', False)]

            domain = expression.AND([domain, start_domain, end_domain])
            if self.search_count(domain):
                raise ValidationError(_('An employee can only have one running contract at the same time. (Excluding Draft, Cancelled and Closed contracts)'))