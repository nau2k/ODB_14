# -*- coding: utf-8 -*-
{
    'name': "Human Resource Management",
    'summary': "The module allows you can create, assign and manage employee.",
    'category': 'Human Resources',
    'version': '1.0.2',
    'author': "DuyBQ, LuanTM",
    "website":  "https://www.odoobase.com/",
    'description': """
        + The module allows you can create, assign and manage employee.
        + Resignation
        + Family
    """,
    'depends': [
        'resource',
        'hr',
        'hr_holidays_attendance',
        'hr_contract',
        'hr_recruitment',
        'erpvn_base',
        'report_xlsx',   
    ],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'data/ir_sequence.xml',
        'data/ir_actions_server.xml',
        'data/ir_cron.xml',
        'data/update_working_hours_history.xml',
        
        
        'reports/ir_actions_report.xml',
        'wizards/wizard_export_employee.xml',

        'views/hr_employee_views.xml',
        'views/hr_employee_type.xml',
        'views/hr_employee_relation_views.xml',
        'views/hr_department_views.xml',
        'views/hr_job_views.xml',
        'views/hr_job_title_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_announcement_view.xml',
        'views/hr_employee_family_views.xml',
        'views/resource_calendar_view.xml',
        'views/res_config_setting.xml',
        'views/menu_view.xml',


        'wizards/wizard_make_contact_view.xml',

        # 'reports/hr_employee_badge.xml',
    ],
    "application": True,
    "installable": True,
    "auto_install": False,


    'post_init_hook': 'post_init_hook',
    'post_init_hook': '_create_history_working_hours',
}
