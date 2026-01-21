import base64
import io
from odoo import models, fields, _, api
from odoo.exceptions import UserError

# Intentamos importar openpyxl (Estándar en Odoo moderno)
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
        """
        Lee el Excel, busca las líneas por ID Externo y actualiza precios/cantidades.
        NO crea líneas nuevas.
        """
        self.ensure_one()
        if not openpyxl:
            raise UserError("La librería openpyxl no está instalada.")

        # 1. Decodificar el archivo binario
        try:
            file_content = base64.b64decode(self.file_data)
            data = io.BytesIO(file_content)
            workbook = openpyxl.load_workbook(data, data_only=True)
            sheet = workbook.active
        except Exception as e:
            raise UserError(f"No se pudo leer el archivo Excel. Error: {e}")

        # 2. Recorrer filas (Saltando la cabecera)
        # Basado en TU estructura de exportación:
        # Col 0 (A): id (Pedido)
        # Col 1 (B): order_line/id (CLAVE)
        # ...
        # Col 7 (H): order_line/product_qty
        # Col 8 (I): order_line/price_unit

        updated_count = 0
        skipped_count = 0

        # iter_rows empieza en 1. min_row=2 salta la cabecera.
        for row in sheet.iter_rows(min_row=2, values_only=True):

            # Obtenemos los datos por índice (0, 1, 2...)
            line_xml_id = row[1]  # Columna B: ID Externo de la línea
            qty = row[7]  # Columna H: Cantidad
            price = row[8]  # Columna I: Precio

            if not line_xml_id:
                skipped_count += 1
                continue

            # 3. BUSCAR LA LÍNEA POR ID EXTERNO (La magia para no duplicar)
            try:
                # self.env.ref convierte "__export__.line_123" en el objeto real de la BD
                line_record = self.env.ref(line_xml_id, raise_if_not_found=False)
            except ValueError:
                # A veces el XML ID viene sucio o mal formado
                line_record = None

            if line_record and line_record._name == 'purchase.order.line':
                # 4. ACTUALIZAR (WRITE)
                # Solo actualizamos si encontramos la línea. Así garantizamos 0 duplicados.
                vals = {}

                # Validamos que sean números para no romper Odoo
                if isinstance(price, (int, float)):
                    vals['price_unit'] = price

                if isinstance(qty, (int, float)):
                    vals['product_qty'] = qty

                if vals:
                    line_record.write(vals)
                    updated_count += 1
            else:
                skipped_count += 1

        # 5. Notificar al usuario
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importación Completada'),
                'message': f'Se actualizaron {updated_count} líneas. Se omitieron {skipped_count}.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }