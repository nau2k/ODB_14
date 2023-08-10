# -*- encoding: utf-8 -*-
{
	'name': 'Time Off Management',
	'category': 'Human Resources/TimeSheet',
	'version': '1.0.2',
	'author': 'DuyBQ, LuanTM, ManhNV',
	'sequence': 100,
    'website': 'https://www.odoobase.com/',
    'license': 'OEEL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
	'depends': [
		'hr_holidays',
		'erpvn_base',
		'erpvn_hr_work_entry'
	],
	'data': [
		'security/res_groups.xml',
		'security/ir.model.access.csv',
		'security/ir_rule.xml',

		'data/mail_template.xml',
		'data/hr_leave_web_portal.xml',
		# 'data/ir_cron.xml',
		'data/ir_sequence.xml',

		'wizards/update_nextcall_allocation_wizard_views.xml',

		'views/hr_leave_allocation_views.xml',
		'views/hr_employee_views.xml',
		'views/hr_leave_mode_type_views.xml',
		'views/hr_leave_type_views.xml',
		'views/hr_leave_views.xml',
		'views/hr_adjustment_request.xml',
		'views/hr_work_entry.xml',
		'views/res_config_settings_view.xml',
		'views/menu_views.xml',
	],
}
