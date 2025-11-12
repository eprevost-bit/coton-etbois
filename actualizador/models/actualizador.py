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


class ContactUpdaterWizard(models.TransientModel):
    _name = 'contact.updater.wizard'
    _description = 'Asistente para Actualizar Posición Fiscal de Contactos'

    file_data = fields.Binary(
        string='Archivo XLSX',
        required=True
    )
    file_name = fields.Char(string='Nombre del Archivo')

    def action_update_contacts(self):
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
        skipped_count = 0
        failed_count = 0
        log_failures = []

        # 2. Iterar por las filas (asumimos cabecera en Fila 1)
        # Asumimos Columna A = Nombre, Columna B = Posición Fiscal
        for row in sheet.iter_rows(min_row=2, values_only=True):
            name = row[0]
            property_account_position_id = row[1]

            if not name or not property_account_position_id:
                continue  # Omitir filas vacías

            # 3. Buscar el Contacto
            contact = self.env['res.partner'].search([
                ('name', '=', name)
            ], limit=1)

            # 4. Buscar la Posición Fiscal
            fiscal_position = self.env['account.fiscal.position'].search([
                ('name', '=', property_account_position_id)
            ], limit=1)

            if not contact:
                _logger.warning(f'Contacto no encontrado: "{name}"')
                failed_count += 1
                log_failures.append(f'Contacto no encontrado: {name}')
                continue

            if not fiscal_position:
                _logger.warning(f'Posición fiscal no encontrada: "{property_account_position_id}"')
                failed_count += 1
                log_failures.append(f'Posición fiscal no encontrada: {property_account_position_id} (para contacto {name})')
                continue

            # 5. Aplicar la LÓGICA REQUERIDA
            # Solo actualiza si el contacto NO tiene una posición fiscal asignada
            if contact and fiscal_position and not contact.property_account_position_id:
                try:
                    # El campo técnico es 'property_account_position_id'
                    contact.write({
                        'property_account_position_id': fiscal_position.id
                    })
                    updated_count += 1
                except Exception as e:
                    _logger.error(f'Error al actualizar {name}: {e}')
                    failed_count += 1
                    log_failures.append(f'Error al escribir en {name}: {e}')
            elif contact.property_account_position_id:
                # El contacto ya tenía una, lo omitimos
                skipped_count += 1

        _logger.info(
            f'Actualización completada. Actualizados: {updated_count}, Omitidos: {skipped_count}, Fallidos: {failed_count}')

        # 6. Devolver una notificación al usuario (opcional pero recomendado)
        message = f"Proceso completado:\n" \
                  f"✅ Contactos actualizados: {updated_count}\n" \
                  f"⏭️ Contactos omitidos (ya tenían PF): {skipped_count}\n" \
                  f"❌ Errores (no encontrados): {failed_count}\n\n"

        if log_failures:
            message += "Detalle de errores:\n" + "\n".join(log_failures[:10])  # Mostrar primeros 10 errores

        # Usamos un 'rainbow_man' para una notificación visual
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Actualización de Contactos'),
                'message': message,
                'sticky': True,  # Para que el usuario deba cerrarla
                'type': 'info' if failed_count == 0 else 'warning',
            }
        }