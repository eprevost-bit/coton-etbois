# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import logging

_logger = logging.getLogger(__name__)

# Intenta importar openpyxl, que Odoo usa para XLSX
try:
    import openpyxl
except ImportError:
    _logger.debug('La librería "openpyxl" no está instalada. Instálala con "pip install openpyxl"')


class ProductDescriptionUpdaterWizard(models.TransientModel):
    _name = 'product.description.updater.wizard'
    _description = 'Asistente para Actualizar Descripción de Productos'

    file_data = fields.Binary(
        string='Archivo XLSX',
        required=True
    )
    file_name = fields.Char(string='Nombre del Archivo')

    def action_update_products(self):
        """
        Esta es la función principal que se ejecuta al presionar el botón.
        """
        if not self.file_data:
            raise UserError(_('Por favor, carga un archivo.'))

        # 1. Decodificar el archivo y leerlo
        try:
            file_content = base64.b64decode(self.file_data)
            workbook = openpyxl.load_workbook(io.BytesIO(file_content))
            sheet = workbook.active
        except Exception as e:
            raise UserError(_('Error al leer el archivo. Asegúrate de que sea un XLSX válido.\nError: %s') % e)

        # Contadores para feedback
        updated_count = 0
        failed_count = 0
        log_failures = []

        # 2. Iterar por las filas (asumimos cabecera en Fila 1)
        # Asumimos Columna A = Nombre del Producto, Columna B = Descripción
        for row in sheet.iter_rows(min_row=2, values_only=True):
            # Asignamos None si la celda está vacía
            name = row[0] if row[0] else None
            description = row[1] if row[1] else '' # Usar '' si la descripción está vacía

            if not name:
                continue  # Omitir filas sin nombre de producto

            # 3. Buscar el Producto
            # Buscamos en 'product.product' (Producto)
            product = self.env['product.product'].search([
                ('name', '=', name)
            ], limit=1)

            # 4. Aplicar la LÓGICA REQUERIDA
            # Si encontramos el producto, actualizamos su descripción
            if product:
                try:
                    product.write({
                        'description': description # Actualizamos el campo 'description'
                    })
                    updated_count += 1
                except Exception as e:
                    _logger.error(f'Error al actualizar {name}: {e}')
                    failed_count += 1
                    log_failures.append(f'Error al escribir en {name}: {e}')
            else:
                # El producto no fue encontrado
                _logger.warning(f'Producto no encontrado: "{name}"')
                failed_count += 1
                log_failures.append(f'Producto no encontrado: {name}')

        _logger.info(
            f'Actualización completada. Actualizados: {updated_count}, Fallidos: {failed_count}')

        # 5. Devolver una notificación al usuario
        message = f"Proceso completado:\n" \
                  f"✅ Productos actualizados: {updated_count}\n" \
                  f"❌ Errores (no encontrados/error): {failed_count}\n\n"

        if log_failures:
            message += "Detalle de errores:\n" + "\n".join(log_failures[:10])  # Mostrar primeros 10 errores

        # Usamos una notificación para el feedback
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Actualización de Productos'),
                'message': message,
                'sticky': True,  # Para que el usuario deba cerrarla
                'type': 'info' if failed_count == 0 else 'warning',
            }
        }