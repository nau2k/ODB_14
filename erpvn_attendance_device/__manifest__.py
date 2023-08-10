{
    'name': 'HR Attendance Device',
    'summary': '''
Integrate attendance devices''',
    'description': '''
Key Features
============
* Support both TCP and UDP
* Compute attendance with 2 option: System or Device
* Designed to work with all attendance devices that based on ZKTeco platform.
    ''',
    'category': 'Human Resources/TimeSheet',
    'version': '1.0.5',
    'author': 'DuyBQ',
    'website': 'https://www.odoobase.com/',
    'license': 'OEEL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'depends': [
        'erpvn_base',
        'hr_attendance',
        'hr_work_entry',
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',

        'data/ir_cron.xml',
        'data/ir_actions_server.xml',
        'data/mail_template_data.xml',
        'data/attendance_state.xml',

        'views/attendance_device_views.xml',
        'views/attendance_device_user_views.xml',
        'views/hr_attendance_views.xml',
        'views/attendance_state_views.xml',
        'views/user_attendance_views.xml',
        'views/finger_template_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',

        'wizard/attendance_wizard.xml',
        'wizard/employee_upload_wizard.xml',

        'views/menu_views.xml',
        'views/web_assets_backend.xml',
    ],
    'external_dependencies': {
        'python': ['datetimerange'],
        'bin': [],
    },
    'post_init_hook': 'post_init_hook',
}
