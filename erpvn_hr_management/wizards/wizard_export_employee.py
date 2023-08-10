# -*- coding: utf-8 -*-
from odoo import fields, models,api, _

class WizardExportEmployee(models.TransientModel):
    _name = "wizard.export.employee"
    _description = "Export Sale Order Wizard"


    import_type = fields.Selection([
        ('select_dep', 'Select Department'),
        ('active', 'Working'),
        ('archive', 'Resigned'),
        ('all','Export All')
    ], default='select_dep', string="Export Type", required=True)
    employee_ids = fields.Many2many('hr.employee', string='Select Employee')
    department_ids = fields.Many2many('hr.department',string="Select Department")

    @api.onchange('import_type')
    def _onchange_import_type(self):
        if self.import_type == 'select_dep':
            self.employee_ids = False
        elif self.import_type in ['active','archive']:
            self.department_ids = False
        elif self.import_type == 'all':
            self.employee_ids = False
            self.department_ids = False

    def action_export_employee(self):
        if self.employee_ids or self.import_type in ['active','archive']:
            employee = self.employee_ids
        elif self.department_ids:
            employee = self.env['hr.employee'].search([('department_id.id','in',self.department_ids.ids),('employee_type_id.name','!=','Machine')],order='department_id')
            if not employee:
                employee = self.department_ids.manager_id
        elif self.import_type =='all':
            employee = self.env['hr.employee'].search([('employee_type_id.name','!=','Machine')],order='department_id')
        data = {
            "ids": employee.ids,
        }
        return self.env["report.erpvn_hr_management.export_employee"].get_action(data)
