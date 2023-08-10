# -*- coding: utf-8 -*-
{
    'name': 'HR Resignation',
    'summary': '',
    'description': '''
        + Manager Employee Resignation
    ''',
    'category': 'Human Resources',
    'version': '1.0.1',
    'author': 'DuyBQ',
    'website': 'https://www.odoobase.com/',
    'license': 'OEEL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
    'depends': [
        'erpvn_base',
        'erpvn_hr_management',
        'report_py3o',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        
        'data/ir_sequence.xml',
        'data/report_py3o.xml',
        'data/ir_cron.xml',
        'data/mail_template.xml',

        'views/hr_resignation_views.xml',
        'views/menu_views.xml',
        
        'wizards/resign_approve.xml',
        'wizards/resign_confirm.xml',
    ],
}
