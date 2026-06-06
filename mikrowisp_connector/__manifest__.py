{
    'name': 'Mikrowisp Connector',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Sincronización de clientes ISP desde Mikrowisp hacia Odoo (solo lectura)',
    'author': 'Nisbe',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
