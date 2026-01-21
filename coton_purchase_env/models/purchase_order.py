from collections import defaultdict

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, groupby
import logging
from itertools import groupby
from ast import literal_eval
from odoo.tools import float_is_zero
import base64
import io
import xlsxwriter

_logger = logging.getLogger(__name__)


class PurchaseOrderLineCustom(models.Model):
    _inherit = 'purchase.order.line'

    # 1. Campo para la casilla de selección en cada línea
    is_selected_for_email = fields.Boolean(string="Seleccionar para Correo")
    proveedor_line = fields.Many2one('res.partner', string='Proveedor')


class PurchaseOrderCustom(models.Model):
    _inherit = 'purchase.order'

    # Redefinimos el campo 'state' para eliminar los estados 'sent' e 'intermediate'
    # y mantener el estado personalizado 'inicial_presu'.
    # Los estados base de Odoo son: draft, sent, to approve, purchase, done, cancel.
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('to approve', 'A Aprobar'),
        ('inicial_presu', 'Presupuesto Inicial'),
        ('purchase', 'Orden de Compra'),
        ('done', 'Bloqueado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', readonly=True, index=True, copy=False, default='draft', tracking=True)

    number = fields.Float(string="numero de acciones")

    def action_set_to_inicial_presupuesto(self):
        all_new_orders = []
        for order in self:
            origin_name = order.origin
            # 1. Agrupar lineas por proveedor
            supplier_lines = defaultdict(lambda: self.env['purchase.order.line'])
            for line in order.order_line:
                if line.proveedor_line:
                    supplier_lines[line.proveedor_line] |= line

            if not supplier_lines:
                # Si no se asignaron proveedores, simplemente cambia el estado y continúa.
                order.write({'state': 'inicial_presu'})
                continue

            # 2. Crear nuevos pedidos de compra
            new_orders_for_current = []
            for supplier, lines in supplier_lines.items():
                # Copiamos el pedido original
                new_order = order.copy({
                    'partner_id': supplier.id,
                    'order_line': [],  # Limpiamos las lineas para no duplicar las originales
                    'state': 'draft',  # Estado inicial para los nuevos pedidos
                })
                new_order.write({'origin': origin_name, 'number': 1})
                # Copiamos solo las lineas correspondientes a este proveedor
                for line in lines:
                    line.copy({
                        'order_id': new_order.id,
                        'x_source_sale_line_id': line.x_source_sale_line_id.id
                    })

                new_orders_for_current.append(new_order.id)

            # 3. Cambiar el estado del pedido original
            if new_orders_for_current:
                order.write({'state': 'inicial_presu'})
                all_new_orders.extend(new_orders_for_current)

        # 4. Opcional: Devolver una acción para ver todos los nuevos pedidos creados
        if all_new_orders:
            tree_view_id = self.env.ref('purchase.purchase_order_tree').id
            form_view_id = self.env.ref('purchase.purchase_order_form').id
            return {
                'name': 'Pedidos de Compra Generados',
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'tree,form',
                'views': [(tree_view_id, 'list'), (form_view_id, 'form')],
                'domain': [('id', 'in', all_new_orders)],
                'target': 'current',  # Abre en la misma pestaña
            }

        return True

    def _generate_excel_attachment(self, selected_lines):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Partidas')

        # Estilos
        bold = workbook.add_format({'bold': True, 'bg_color': '#f2f2f2', 'border': 1})
        border = workbook.add_format({'border': 1})
        currency_style = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})

        # Cabeceras
        headers = ['Producto', 'Descripción', 'Cantidad', 'UdM', 'Precio Estimado (Subtotal)']
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, bold)
            sheet.set_column(col_num, col_num, 20)  # Ajustar ancho

        # Datos
        row = 1
        for line in selected_lines:
            sheet.write(row, 0, line.product_id.name, border)
            sheet.write(row, 1, line.name, border)
            sheet.write(row, 2, line.product_qty, border)
            sheet.write(row, 3, line.product_uom_id.name or '', border)
            sheet.write(row, 4, line.price_subtotal, currency_style)
            row += 1

        workbook.close()
        output.seek(0)
        file_content = base64.b64encode(output.read())
        output.close()

        # Crear el adjunto en Odoo
        attachment = self.env['ir.attachment'].create({
            'name': f'Solicitud_{self.name}.xlsx',
            'type': 'binary',
            'datas': file_content,
            'res_model': 'purchase.order',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        return attachment.id

    def _generate_importable_excel(self, selected_lines):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Import_Export')

        # Formatos
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#d9d9d9', 'border': 1})
        date_fmt = workbook.add_format({'num_format': 'yyyy-mm-dd'})

        # 1. Definir columnas: ¡LA SEGUNDA COLUMNA ES LA CLAVE!
        headers = [
            'id',
            'order_line/id',
            'name',
            'partner_id',
            'date_order',
            'order_line/product_id',
            'order_line/name',
            'order_line/product_qty',
            'order_line/price_unit',
        ]

        # Escribir Cabeceras
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, header_fmt)
            sheet.set_column(col_num, col_num, 25)

        # 2. Obtener ID del Pedido (Cabecera)
        # Si no tiene ID externo, creamos uno estable usando "__export__"
        external_ids = self.get_external_id()
        xml_id = external_ids.get(self.id) or f"__export__.purchase_order_{self.id}"

        # Datos comunes
        po_name = self.name
        po_partner = self.partner_id.name
        po_date = self.date_order

        # 3. Escribir las líneas
        row = 1
        for line in selected_lines:
            # --- GENERACIÓN DEL ID DE LÍNEA ---
            # Buscamos si la línea ya tiene un ID externo real
            line_ext_ids = line.get_external_id()
            # Si no tiene, inventamos uno FIJO usando su ID de base de datos.
            # Al ser fijo, Odoo sabrá que es la misma línea al importar.
            line_xml_id = line_ext_ids.get(line.id) or f"__export__.purchase_order_line_{line.id}"
            # ----------------------------------

            # Escribir datos
            sheet.write(row, 0, xml_id)  # Col A: ID del Pedido
            sheet.write(row, 1, line_xml_id)  # Col B: ID de la Línea (IMPORTANTE)
            sheet.write(row, 2, po_name)
            sheet.write(row, 3, po_partner)
            sheet.write_datetime(row, 4, po_date, date_fmt)

            # Datos de la línea
            sheet.write(row, 5, line.product_id.display_name or '')
            sheet.write(row, 6, line.name)
            sheet.write(row, 7, line.product_qty)
            sheet.write(row, 8, line.price_unit)

            row += 1

        workbook.close()
        output.seek(0)
        file_content = base64.b64encode(output.read())
        output.close()

        # Crear adjunto
        attachment = self.env['ir.attachment'].create({
            'name': f'Exportacion_Sistema_{self.name}.xlsx',
            'type': 'binary',
            'datas': file_content,
            'res_model': 'purchase.order',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        return attachment.id

    def action_send_items_by_email(self):
        self.ensure_one()
        selected_lines = self.order_line.filtered(lambda line: line.is_selected_for_email)

        if not selected_lines:
            raise UserError("Por favor, seleccione al menos una partida.")

        # 1. Generar Excel VISUAL (Para el proveedor)
        attachment_visual_id = self._generate_excel_attachment(selected_lines)

        # 2. Generar Excel DE SISTEMA (Para importar)
        attachment_import_id = self._generate_importable_excel(selected_lines)

        template = self.env.ref('coton_purchase_env.email_template_purchase_selected_lines')

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_model': 'purchase.order',
                'default_res_ids': [self.id],
                'default_use_template': True,
                'default_template_id': template.id,
                # AQUÍ PASAMOS LOS DOS IDs
                'default_attachment_ids': [(6, 0, [attachment_visual_id, attachment_import_id])],
                'selected_line_ids': selected_lines.ids
            },
        }

    def action_send_items_with_price(self):
        self.ensure_one()
        selected_lines = self.order_line.filtered(lambda line: line.is_selected_for_email)

        if not selected_lines:
            raise UserError("Por favor, seleccione al menos una partida.")

        # 1. Generar Excel VISUAL
        attachment_visual_id = self._generate_excel_attachment(selected_lines)

        # 2. Generar Excel DE SISTEMA
        attachment_import_id = self._generate_importable_excel(selected_lines)

        template = self.env.ref('coton_purchase_env.email_template_purchase_selected_lines_price')

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_model': 'purchase.order',
                'default_res_ids': [self.id],
                'default_use_template': True,
                'default_template_id': template.id,
                # AQUÍ PASAMOS LOS DOS IDs
                'default_attachment_ids': [(6, 0, [attachment_visual_id, attachment_import_id])],
                'selected_line_ids': selected_lines.ids
            },
        }

    def action_create_invoice(self):
        """Create the invoice associated to the PO."""
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        invoice_vals_list = []
        sequence = 10

        _logger.info(f"--- INICIO ACTION_CREATE_INVOICE para {len(self)} ordenes ---")

        for order in self:
            # LOG PARA VER EL ESTADO
            _logger.info(
                f"Orden: {order.name}, Estado Facturación: {order.invoice_status}, Estado Orden: {order.state}")

            if order.invoice_status != 'to invoice':
                _logger.warning(f"SALTANDO Orden {order.name} porque su status no es 'to invoice'")
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            invoice_vals = order._prepare_invoice()

            lines_added = 0
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue

                # LOG PARA VER CANTIDADES
                qty_to_invoice = line.product_qty - line.qty_invoiced
                _logger.info(
                    f"Line {line.name}: Qty total: {line.product_qty}, Invoiced: {line.qty_invoiced}, To Invoice: {qty_to_invoice}")

                if not float_is_zero(qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        line_vals = pending_section._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                        pending_section = None
                    line_vals = line._prepare_account_move_line()
                    line_vals.update({'sequence': sequence})
                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1
                    lines_added += 1

            if lines_added > 0:
                invoice_vals_list.append(invoice_vals)
            else:
                _logger.warning(f"Orden {order.name} no agregó líneas a la factura (posiblemente qty_to_invoice es 0)")

        _logger.info(f"Se generarán {len(invoice_vals_list)} facturas.")

        # --- LÓGICA DE AGRUPACIÓN (IGUAL QUE ANTES) ---
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list,
                                               key=lambda x: (x.get('company_id'), x.get('partner_id'),
                                                              x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals.get('invoice_origin', ''))
                payment_ref = invoice_vals.get('payment_reference')
                if payment_ref: payment_refs.add(payment_ref)
                ref = invoice_vals.get('ref')
                if ref: refs.add(ref)

            ref_invoice_vals.update({
                'ref': ', '.join(filter(None, refs))[:2000],
                'invoice_origin': ', '.join(filter(None, origins)),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Refunds conversion
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_move_type()

        if not moves:
            _logger.error("NO SE CREARON MOVES. Retornando acción vacía o notificación.")
            # Opcional: Retornar una notificación al usuario de que no había nada que facturar
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Atención',
                    'message': 'No hay líneas facturables para las órdenes seleccionadas.',
                    'sticky': False,
                    'type': 'warning',
                }
            }

        # --- RETORNO MANUAL DE LA ACCIÓN ---
        action = self.env["ir.actions.act_window"]._for_xml_id("account.action_move_in_invoice_type")
        if 'context' not in action:
            action['context'] = {}
        elif isinstance(action['context'], str):
            try:
                action['context'] = literal_eval(action['context'])
            except:
                action['context'] = {}

        if len(moves) > 1:
            action['domain'] = [('id', 'in', moves.ids)]
        elif len(moves) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = moves.id

        action['context'].update({
            'default_move_type': 'in_invoice',
            'create': False,
        })

        return action