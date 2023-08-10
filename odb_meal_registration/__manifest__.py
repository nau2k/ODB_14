# -*- coding: utf-8 -*-
{
    'name':  'HR Meal Registration',
    'summary': 'HR Meal Registration',
    'description': '''
        + Manager Employee Registry Meal
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
    ],
    'data': [
        'security/ir.model.access.csv',

        'data/ir_sequence.xml',

        'views/hr_meal_views.xml',
        'views/menu_views.xml',
        'views/res_config_settings_view.xml',
    ],
}
