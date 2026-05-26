# -*- coding: utf-8 -*-
{
    'name': "Service Request",
    'version': "18.0.1.1",
    'License': "LGPL-3",
    'author' : "Fidha",
    'depends': ['base', 'mail','project'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/service_request_views.xml',
        'data/mail_template.xml',
        'data/ir_cron.xml',
        'data/ir_sequence_data.xml',
        'views/res_config_settings_view.xml',
        'views/service_request_menu_views.xml',
    ],


    'application': True,
    'auto_install': True,
    'installable': True,
    'sequence': 1,
}