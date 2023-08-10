{
    'name': "HR Manufacture",

    'summary': """
        Base module HR Manufacture
    """,
    'description': """
        Additional
            + Department
            + Section
            + Job
    """,
    'author': "DuyBQ",
    'website': 'https://www.odoobase.com/',
    'category': 'Human Resources',
    'version': '1.0.1',
    'depends': [
        'resource',
        'erpvn_mrp_management',
        'erpvn_hr_break_time',
        'erpvn_hr_management', 
    ],
    'data': [
        'security/ir.model.access.csv',

        'data/ir_actions_server.xml',

        'wizards/block_reason_wizard_views.xml',
        
        'views/mrp_bom_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/mrp_workorder_views.xml',
        'views/resource_resource_views.xml',
        'views/resource_calendar_leaves_views.xml',
        'views/mrp_workingtime_workcenter_views.xml',
        'views/mrp_routing_workcenter_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True, 
    'auto_install': False,
}
