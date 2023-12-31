# -*- coding: utf-8 -*-
{
    'name':  'HR Move',
    'summary': 'HR Move',
    'description': '''
    ''',
    'category':
    'Human Resources',
    'version': '1.0.1',
    'author': 'ThuanTL',
    'website': 'https://www.odoobase.com/',
    'license':  'OEEL-1',
    'installable':  True,
    'auto_install':  False,
    'application':    False,
    'depends': [
        'erpvn_base', 
        'erpvn_hr_leave_management',
        "report_py3o",
    ],
    'data': [
        'security/ir.model.access.csv',

        'data/ir_sequence.xml',
        'data/mail_template.xml',
        'data/report_py3o.xml',
    
        'views/hr_move_views.xml',
        'views/menu_views.xml',
 
    ],
}
