# -*- coding: utf-8 -*-
{
    'name':  'HR VietNam State',
    'summary':
    '',
    'category':
    'Human Resources',
    'version': '1.0.1',
    'author': 'ThuanTL',
    'website': 'https://www.odoobase.com/',
    'license':  'OEEL-1',
    'installable':  True,
    'auto_install':  False,
    'application':    False,
    'depends': ['hr','erpvn_hr_management', 'erpvn_vietnam_state'],
    'data': [
        'views/hr_employee.xml',
    ],
}
