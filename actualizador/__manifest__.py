{
    'name': 'Actualizador de Posiciones Fiscales',
    'version': '1.0',
    'summary': 'Actualiza posiciones fiscales de contactos desde un XLSX.',
    'author': 'Tu Nombre',
    'depends': ['base', 'account', 'contacts','sale_management','sale'], # 'account' es clave
    'data': [
        'security/ir.model.access.csv', # ¡No olvides la seguridad!
        'views/actualizador_views.xml',
		'views/actualizador_products_view.xml',
],
    'installable': True,
    'application': False,
}