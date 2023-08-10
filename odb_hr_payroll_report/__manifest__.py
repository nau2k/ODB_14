# -*- coding: utf-8 -*-
{
    'name': 'HR Payroll Report',
    'summary': 'A payroll report',
    'category': 'Human Resources/Payroll',
    'version': '1.0.1',
    'author': 'DuyBQ',
    'website': 'https://www.odoobase.com/',
    'license': 'OEEL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
    'depends': [
        'erpvn_hr_payroll',
        'erpvn_hr_payroll_vn',
        'report_xlsx',
    ],
    'data': [
        'report/payroll_report.xml',
    ],
}