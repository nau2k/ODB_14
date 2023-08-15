# -*- coding: utf-8 -*-
{
    'name':  'HR Transfer',
    'summary': 'HR Transfer',
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
      
    ],
    'data': [
        'security/ir.model.access.csv',

      
        'views/hr_transfer_views.xml',
        'views/menu_views.xml',
 
    ],
}
