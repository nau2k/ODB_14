# -*- coding: utf-8 -*-
from odoo import models, fields


class HRPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(help="Gives the sequence when displaying a list of Contract.", default=10)
    count_working_seniority = fields.Boolean(string='Working Seniority', default=False,
        help="The contracts which activate this field will be taken into account the calculation of working seniority")
    allowance_ids = fields.One2many('hr.contract.allowance', 'contract_type_id', 'Allowance Template')
