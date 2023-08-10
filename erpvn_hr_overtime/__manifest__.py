# -*- coding: utf-8 -*-
{
    'name': 'HR Overtime',
    'summary': 'Manage Employee Overtime',
    'description': '''Helps you to manage Employee Overtime.''',
    'category': 'Human Resources/TimeSheet',
    'version': '1.0.1',
    'author': 'DuyBQ',
    'website': 'https://www.odoobase.com/',
    'sequence': 15,
    'installable': True,
    'auto_install': False,
    'application': False,
    'depends': [
        'hr_holidays',
        'erpvn_hr_mrp',
        'erpvn_hr_work_entry',
    ],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'data/mail_template.xml',
        
        'views/resouce_overtime.xml',
        'views/hr_overtime_type_view.xml',
        'views/hr_overtime_view.xml',
        'views/hr_overtime_line_view.xml',
        'views/res_config_settings_view.xml',
        'views/menu_view.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'demo': ['demo/hr_overtime.xml'],
}
