from collections import defaultdict

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, groupby
from itertools import groupby
from ast import literal_eval


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

    def action_send_items_by_email(self):
        self.ensure_one()

        # 2. Filtrar para obtener solo las líneas que el usuario seleccionó
        selected_lines = self.order_line.filtered(lambda line: line.is_selected_for_email)

        if not selected_lines:
            raise UserError("Por favor, seleccione al menos una partida para enviar por correo electrónico.")

        # 3. Cargar la plantilla de correo que crearemos en el siguiente paso
        template = self.env.ref('coton_purchase_env.email_template_purchase_selected_lines')

        # 4. Abrir el pop-up del correo electrónico (compositor de correo)
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': {
                'default_model': 'purchase.order',
                'default_res_ids': [self.id],
                'default_use_template': True,
                'default_template_id': template.id,
                'selected_line_ids': selected_lines.ids
            },
        }

    def action_create_invoice(self):
        """Create the invoice associated to the PO."""
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        sequence = 10
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            invoice_vals = order._prepare_invoice()

            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                qty_to_invoice = line.product_qty - line.qty_invoiced

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
            invoice_vals_list.append(invoice_vals)

        # Agrupación de facturas (Tu lógica personalizada)
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
                if payment_ref:
                    payment_refs.add(payment_ref)

                ref = invoice_vals.get('ref')
                if ref:
                    refs.add(ref)

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

        # 4) Convert negative totals to refunds
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_move_type()

        # --- CORRECCIÓN DEL ERROR ODOO 19 ---
        # En lugar de llamar a self.action_view_invoice(moves), construimos la acción manualmente
        # para evitar el KeyError: 'context' del código base inestable.

        action = self.env["ir.actions.act_window"]._for_xml_id("account.action_move_in_invoice_type")

        # 1. Manejo seguro del 'context' (Aquí es donde fallaba Odoo)
        if 'context' not in action:
            action['context'] = {}
        elif isinstance(action['context'], str):
            # Si viene como string, intentamos evaluarlo, si falla lo dejamos vacío
            try:
                action['context'] = literal_eval(action['context'])
            except:
                action['context'] = {}

        # 2. Definir qué facturas mostrar
        if len(moves) > 1:
            action['domain'] = [('id', 'in', moves.ids)]
        elif len(moves) == 1:
            # Si es solo una, redirigimos directamente a la vista formulario
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = moves.id

        # 3. Inyectar contexto necesario
        action['context'].update({
            'default_move_type': 'in_invoice',
            'create': False,
        })

        return action
