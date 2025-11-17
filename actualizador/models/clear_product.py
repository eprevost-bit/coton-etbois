# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ProductDescriptionCleanerWizard(models.TransientModel):
    _name = 'product.description.cleaner.wizard'
    _description = 'Asistente para Limpiar Descripciones de Productos'

    # Mensaje informativo para que el usuario sepa qué va a pasar
    info_text = fields.Text(
        string="Información",
        default="Al ejecutar este proceso, se borrará el contenido del campo 'Descripción' de TODOS los productos en el sistema. Esta acción no se puede deshacer.",
        readonly=True
    )

    def action_clean_descriptions(self):
        """
        Busca todos los productos y vacía su descripción.
        """
        # 1. Definir en qué modelo buscar.
        # Normalmente las descripciones están en 'product.template'
        ProductTemplate = self.env['product.template']

        # 2. Buscar productos que SÍ tengan descripción (para no escribir en balde)
        # NOTA: 'description' son las "Notas Internas".
        # Si quieres borrar la descripción de ventas, usa 'description_sale'
        products_to_clean = ProductTemplate.search([
            ('description', '!=', False)
        ])

        # Si quieres borrar también los que tienen descripción de venta, descomenta esto:
        # products_to_clean = ProductTemplate.search([
        #     '|',
        #     ('description', '!=', False),
        #     ('description_sale', '!=', False)
        # ])

        count = len(products_to_clean)

        if count == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Nada que limpiar'),
                    'message': 'No se encontraron productos con descripciones.',
                    'type': 'info',
                }
            }

        # 3. Borrado Masivo (Optimizado)
        # En lugar de un bucle 'for', le decimos a Odoo que escriba en todos a la vez.
        try:
            products_to_clean.write({
                'description': False,  # Borra Notas Internas
                # 'description_sale': False,  # Descomenta para borrar Descripción Ventas
                # 'description_purchase': False # Descomenta para borrar Descripción Compras
            })

            _logger.info(f'Limpieza completada. Productos afectados: {count}')

        except Exception as e:
            _logger.error(f"Error durante la limpieza masiva: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': f'Ocurrió un error: {str(e)}',
                    'sticky': True,
                    'type': 'danger',
                }
            }

        # 4. Notificación de éxito
        message = f"✅ Proceso completado.\nSe ha eliminado la descripción de {count} productos."

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Limpieza Finalizada'),
                'message': message,
                'sticky': False,
                'type': 'success',
            }
        }