import base64
import io
import logging
from odoo import models, fields, _, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import openpyxl
except ImportError:
    openpyxl = None


class PurchaseImportWizard(models.TransientModel):
    _name = 'purchase.import.wizard'
    _description = 'Asistente para Importar Precios de Compra'

    file_data = fields.Binary(string='Archivo Excel', required=True)
    file_name = fields.Char(string='Nombre del archivo')
    purchase_id = fields.Many2one('purchase.order', string='Pedido de Compra')

    def action_import_lines(self):
        self.ensure_one()
        if not openpyxl:
            raise UserError("La librería openpyxl no está instalada.")

        try:
            file_content = base64.b64decode(self.file_data)
            data = io.BytesIO(file_content)
            workbook = openpyxl.load_workbook(data, data_only=True)
            sheet = workbook.active
        except Exception as e:
            raise UserError(f"No se pudo leer el archivo Excel. Error: {e}")

        updated_count = 0
        skipped_count = 0

        # LOG: Para ver qué está pasando en la consola del servidor
        _logger.info(">>> INICIANDO IMPORTACIÓN DE LÍNEAS DE COMPRA <<<")

        # Recorremos filas. start=2 es solo para el log (fila visual de excel)
        for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):

            # --- MAPEO DE COLUMNAS (Asegúrate que coincida con tu exportación) ---
            # Col B (Indice 1): order_line/id
            # Col H (Indice 7): order_line/product_qty
            # Col I (Indice 8): order_line/price_unit

            line_xml_id = row[1]
            qty_raw = row[7]
            price_raw = row[8]

            # 1. Limpieza del ID
            if not line_xml_id:
                _logger.info(f"Fila {idx}: Saltada (No hay ID externo)")
                skipped_count += 1
                continue

            # Asegurar que el ID es texto y quitar espacios sobrantes
            line_xml_id = str(line_xml_id).strip()

            # 2. Buscar la línea en Odoo
            try:
                line_record = self.env.ref(line_xml_id, raise_if_not_found=False)
            except ValueError:
                line_record = None

            if not line_record:
                _logger.warning(f"Fila {idx}: ID '{line_xml_id}' no encontrado en Odoo.")
                skipped_count += 1
                continue

            # Verificar que sea realmente una línea de compra
            if line_record._name != 'purchase.order.line':
                _logger.warning(f"Fila {idx}: El ID '{line_xml_id}' no es una línea de compra.")
                skipped_count += 1
                continue

            # 3. Preparar valores (CORRECCIÓN PRINCIPAL AQUÍ)
            vals = {}

            # --- Procesar PRECIO ---
            if price_raw is not None:
                try:
                    # Intentamos convertir a float, sea texto o número
                    vals['price_unit'] = float(price_raw)
                except (ValueError, TypeError):
                    _logger.warning(f"Fila {idx}: El precio '{price_raw}' no es un número válido.")

            # --- Procesar CANTIDAD ---
            if qty_raw is not None:
                try:
                    vals['product_qty'] = float(qty_raw)
                except (ValueError, TypeError):
                    pass  # Si falla la cantidad, ignoramos pero seguimos con el precio

            # 4. Escribir cambios
            if vals:
                try:
                    line_record.write(vals)
                    updated_count += 1
                    _logger.info(f"Fila {idx}: Actualizada OK. ID: {line_xml_id} -> {vals}")
                except Exception as e:
                    _logger.error(f"Fila {idx}: Error al escribir en Odoo: {e}")
                    skipped_count += 1
            else:
                _logger.info(f"Fila {idx}: Saltada (Sin cambios válidos)")
                skipped_count += 1

        _logger.info(f">>> FIN IMPORTACIÓN: Actualizados {updated_count}, Omitidos {skipped_count} <<<")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importación Completada'),
                'message': f'Se actualizaron {updated_count} líneas. Se omitieron {skipped_count}. Revisar logs si hay errores.',
                'type': 'success' if updated_count > 0 else 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }