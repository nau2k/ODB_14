# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HRMealLine(models.Model):
    _name = 'hr.meal.line'

    meal_id = fields.Many2one('hr.meal', string='Meal', ondelete='cascade')
    barcode = fields.Char(related='employee_id.barcode')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department',string="Department",store=True,related='employee_id.department_id' )
    is_registry = fields.Boolean(default=True,string='Registry') 
    date_start = fields.Date('From', related='meal_id.date_start', store=True)
    date_end = fields.Date('To', related='meal_id.date_end', store=True)
    state_meals = fields.Selection(related='meal_id.state', store=True)
    state = fields.Selection([('validated', 'Validated'),('duplicated','Duplicate employee'),('cancel', 'Cancelled')], default='validated', string='State')

    _sql_constraints = [
        ("employee_meal_uniq", "unique (employee_id, meal_id)", "Duplicate employee found for this meal.")
    ]

    @api.onchange('employee_id')
    def _domain_empaloyee(self):
        list_employee_id =self.env['hr.employee'].search([('id', 'not in',self.meal_id.employee_meal_line.employee_id.ids)])
        if len(list_employee_id)> 0:
            return {'domain': {'employee_id': [('id' , 'in' , list_employee_id.ids)]}}
        else:
            return {'domain': {'employee_id': [('id' , 'in' , False)]}}

    @api.model
    def create(self, vals):
        res = super(HRMealLine, self).create(vals)
        date_start = vals.get('date_start') or res.meal_id.date_start
        date_end = vals.get('date_end') or res.meal_id.date_end

        existing_records = self.search([
            ('id', '!=', res.id),
            ('state_meals','!=','cancel'),
            ('employee_id', '=', vals.get('employee_id')),
            ('date_start', '<=', date_end),
            ('date_end', '>=', date_start),
        ],limit=1)

        if existing_records:
            res.state = 'duplicated'
            res.is_registry = existing_records.is_registry
        else:
            res.state = 'validated'

        return res
