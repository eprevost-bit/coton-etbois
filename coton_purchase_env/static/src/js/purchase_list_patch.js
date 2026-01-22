/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
    },

    get cogItems() {
        // Obtenemos los items originales (Exportar, Importar registros, etc.)
        const items = super.cogItems;

        // VERIFICACIÓN IMPORTANTE: Solo mostrar en Compras
        // Si no pones esto, el botón saldrá en Ventas, Inventario, Contactos, etc.
        if (this.props.resModel === 'purchase.order') {

            items.push({
                name: "import_excel_global",
                description: "📥 Importar Precios (Excel)", // Texto que ve el usuario
                action: () => {
                    // AQUÍ LLAMAMOS A TU XML
                    // Reemplaza 'tu_modulo' con el nombre técnico de tu carpeta
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },
            });
        }

        return items;
    }
});