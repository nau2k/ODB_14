# -*- coding: utf-8 -*-
{
    "name": "HR Contract",
    'version': '1.0.1',
    "author": "DuyBQ",
    "website": "https://www.odoobase.com/",
    'category': 'Human Resources',
    "depends": [
        "hr_contract",
        "erpvn_base",
        "report_py3o",
    ],
    'data': [
        # "data/ir_sequence_data.xml",

        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'data/hr_payroll_structure_type.xml',
        'data/report_py3o.xml',

        'wizards/wizard_hr_subcontract_view.xml',
        'wizards/wizard_hr_contract_view.xml',
        'wizards/wizard_py3o.xml',
        
        'views/hr_contract_type_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_subcontract_view.xml',
        'views/hr_contract_allowance.xml',
        'views/hr_payroll_structure_type_view.xml',
        'views/hr_employee.xml',

        'views/menu_view.xml',
    ],
    'installable': True,
}
