{
    'name': "Base Core",

    'summary': """
    Additional tools and utilities for other modules
        + Define name_search
        + Remove decimal zero trailing from float and monetary fields
""",

    'description': """
Base module that provides additional tools and utilities for developers.
    + Remove decimal zero trailing from float and monetary fields
    """,

    'author': "DuyBQ",
    'website': 'https://www.odoobase.com/',
    'category': 'Technical',
    'version': '1.0.4',
    'depends': [
        'base',
        'base_setup',
        'web',
        'mail',
    ],
    'external_dependencies': {
        'python': ['paramiko'],
    },
    'data': [
        'security/res_group.xml',
        'security/ir.model.access.csv',

        'data/res_currency_data.xml',
        'data/send_mail_automation_cron.xml',

        'actions/ir_attachment.xml',

        'wizards/message_wizard_view.xml',

        'views/ir_attachment.xml',
        'views/ir_module_module_view.xml',
        'views/res_currency.xml',
        'views/res_partner.xml',
        'views/mixins_groups.xml',
        'views/formula_model_views.xml',
        'views/res_config_settings.xml',
        'views/web_assets_backend.xml',
    ],
    'qweb': ['static/xml/*.xml'],

    'application': False,
    'installable': True,
    'auto_install': True,
}
