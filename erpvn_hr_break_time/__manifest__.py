# -*- coding: utf-8 -*-
{
    'name': "HR Break Time",
    'summary': """Easily create and manage Break Time for Employee/Worker by Department.""",
    'description': """Easily create and manage Break Time for Employee/Worker by Department.""",
    'version': '1.0.1',
    'website': "https://www.odoobase.com/",
    'category': 'Human Resources/TimeSheet',
    'sequence': 15,
    'installable': True,
    'auto_install': False,
    'application': False,
    'depends': [
        'hr',
        'hr_attendance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'data/mail_template.xml',

        'views/hr_break_time_line_view.xml',
        'views/hr_break_time_view.xml',
        'views/menu_view.xml',
    ],
    'installable': True,
    'application': True,
}
