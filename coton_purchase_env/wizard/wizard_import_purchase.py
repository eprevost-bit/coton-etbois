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

        # 1. Leer el archivo Excel
        try:
            file_content = base64.b64decode(self.file_data)
            data = io.BytesIO(file_content)
            workbook = openpyxl.load_workbook(data, data_only=True)
            sheet = workbook.active
        except Exception as e:
            raise UserError(f"Error al leer el archivo: {e}")

        # 2. Mapeo Dinámico de Columnas
        header_iterator = sheet.iter_rows(min_row=1, max_row=1, values_only=True)
        try:
            headers = next(header_iterator)
        except StopIteration:
            raise UserError("El archivo Excel parece estar vacío.")

        col_map = {str(h).strip(): i for i, h in enumerate(headers) if h}

        # Verificar columna obligatoria
        if 'order_line/id' not in col_map:
            raise UserError("No se encuentra la columna 'order_line/id' en el Excel.")

        idx_xml_id = col_map['order_line/id']
        idx_price = col_map.get('order_line/price_unit')
        idx_qty = col_map.get('order_line/product_qty')

        updated_count = 0
        skipped_count = 0

        # 3. Recorrer y Actualizar
        for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):

            line_xml_id = row[idx_xml_id]

            if not line_xml_id:
                skipped_count += 1
                continue

            line_xml_id = str(line_xml_id).strip()
            line_record = None

            # --- ESTRATEGIA DE BÚSQUEDA ROBUSTA ---

            # Intento A: Buscar como ID Externo Real (xml_id)
            try:
                line_record = self.env.ref(line_xml_id, raise_if_not_found=False)
            except ValueError:
                pass

            # Intento B: Si falló A, intentar extraer el ID numérico del string generado manualmente
            # Tu exportador genera: "__export__.purchase_order_line_{ID}"
            if not line_record and "__export__.purchase_order_line_" in line_xml_id:
                try:
                    # Extraemos el número final: "line_99" -> 99
                    db_id = int(line_xml_id.split('_')[-1])
                    # Buscamos directamente en la tabla por ID numérico
                    line_record = self.env['purchase.order.line'].browse(db_id)

                    # Verificamos si existe (por si fue borrada)
                    if not line_record.exists():
                        line_record = None
                except Exception as e:
                    _logger.warning(f"Error al parsear ID manual en fila {i}: {e}")
                    line_record = None

            # --------------------------------------

            if not line_record:
                _logger.warning(f"Fila {i}: ID '{line_xml_id}' NO encontrado ni como XML_ID ni como ID Database.")
                skipped_count += 1
                continue

            # Preparar valores
            vals = {}

            # Precio
            if idx_price is not None:
                raw_price = row[idx_price]
                if raw_price is not None:
                    try:
                        vals['price_unit'] = float(raw_price)
                    except ValueError:
                        pass

            # Cantidad
            if idx_qty is not None:
                raw_qty = row[idx_qty]
                if raw_qty is not None:
                    try:
                        vals['product_qty'] = float(raw_qty)
                    except ValueError:
                        pass

            # Escribir
            if vals:
                line_record.write(vals)
                updated_count += 1
            else:
                skipped_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Proceso Terminado'),
                'message': f'✅ Actualizadas: {updated_count}\n❌ Omitidas/No encontradas: {skipped_count}',
                'type': 'success' if updated_count > 0 else 'warning',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }