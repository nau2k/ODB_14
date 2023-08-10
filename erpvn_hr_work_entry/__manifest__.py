# -*- coding: utf-8 -*-
{
    'name': "HR Work Entry",
    'summary': """Easily create, manage, and track employee shift schedules.""",
    'description': """Easily create, manage, and track employee shift schedules.""",
    'category': 'Human Resources/TimeSheet',
    'version': '1.0.3',
    'author': 'DuyBQ',
    'website': "https://www.odoobase.com/",
    'depends': [
        'hr_attendance',
        'hr_work_entry',
        'erpvn_hr_contract',
        'erpvn_hr_break_time',
        'erpvn_hr_management',
        'erpvn_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'data/hr_work_entry_type.xml',
        'data/mail_template.xml',
        'data/ir_actions_server.xml',
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        
        'wizards/wizard_validate_work_entry_view.xml',
        'wizards/wizards_adjustment_request_line_view.xml',
        'wizards/attendance_update_wizard.xml',
        'wizards/wizard_open_timesheet.xml',

        'reports/action_report.xml',
        'reports/report_timesheet.xml',
        
        'views/resource_calendar_view.xml',
        'views/hr_work_entry_type_view.xml',
        'views/hr_work_entry_view.xml',
        'views/timesheet_adjustment_request_line_view.xml',
        'views/timesheet_adjustment_request_view.xml',
        'views/hr_attendance_view.xml',
        'views/hr_attendance_late_view.xml',
        'views/hr_employee_public_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_shift_change_order_views.xml',
        'views/hr_shift_change_line_views.xml',
        'views/menu_view.xml',
        'views/web_assets_backend.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'demo': [
        'demo/shift_schedule_data.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
}
