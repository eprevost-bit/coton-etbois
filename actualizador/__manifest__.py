{
    'name': 'Actualizador de Posiciones Fiscales',
    'version': '1.0',
    'summary': 'Actualiza posiciones fiscales de contactos desde un XLSX.',
    'author': 'Tu Nombre',
    'depends': ['base', 'account', 'contacts'], # 'account' es clave
    'data': [
        'security/ir.model.access.csv', # ¡No olvides la seguridad!
        'views/actualizador_views.xml',
    ],
    'installable': True,
    'application': False,
}