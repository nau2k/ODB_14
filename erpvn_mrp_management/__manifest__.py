# -*- coding: utf-8 -*-
{
    'name': "MRP Management",
    'summary': """
        MRP Extended""",
    'description': """
        Help you easy manage production.
    """,
    'author': "DuyBQ",
    "website":  "https://www.odoobase.com/",
    'category': 'Manufacturing',
    'version': '1.0.1',
    'depends': [
        'erpvn_base',
        'mrp_subcontracting',
    ],
    'data': [
        'security/res_groups.xml',
        'data/mail_data.xml',
        'security/ir.model.access.csv',

        'data/ir_cron.xml',
        'data/ir_actions_server.xml',
        'data/ir_action_report.xml',
        'data/ir_sequence.xml',

        'wizards/mrp_bom_selection_wizard_views.xml',
        'wizards/stock_picking_wizard_views.xml',
        'wizards/print_picking_wizard.xml',

        'views/bom_extra_plan_views.xml',
        'views/mrp_workcenter.xml',
        'views/mrp_production.xml',
        'views/mrp_routing_workcenter.xml',
        'views/mrp_bom.xml',
        'views/mrp_operation.xml',
        'views/mrp_workingtime_workcenter.xml',
        'views/mrp_workorder_views.xml',
        'views/mrp_component_line.xml',
        'views/mrp_workcenter_productivity.xml',
        'views/product_category_view.xml',
        'views/stock_move.xml',
        'views/menu_views.xml',
    ],

    'installable': True,
    'application': True,
}
