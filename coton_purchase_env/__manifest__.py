{
    'name': 'Botones Personalizados de Compra',
    'version': '1.0',
    'summary': 'Oculta el botón "Enviar correo electrónico" y añade "Enviar partidas por correo electrónico".',
    'author': 'Tu Nombre',
    'category': 'Purchases',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'data/mail_template_data.xml',
        'data/email_template_purchase_selected_lines_price.xml',
        'views/purchase_order_line.xml',
        'wizard/wizard_import_purchase.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'coton-etbois/static/src/js/purchase_list_patch.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
