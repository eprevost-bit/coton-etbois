/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
    },

    getStaticActionMenuItems() {
        // 1. Obtenemos el MENÚ MAESTRO (que es un Objeto {})
        const items = super.getStaticActionMenuItems();

        // 2. Solo actuamos en Compras
        if (this.props.resModel === 'purchase.order') {

            console.log("⚙️ INYECTANDO BOTÓN EN EL MENÚ MAESTRO...");

            // 3. Insertamos tu botón como una PROPIEDAD del objeto (sin .push)
            // Usamos una clave única 'custom_import_excel'
            items.custom_import_excel = {
                // Texto que sale en el menú
                description: "📥 Importar Precios (Excel)",

                // Acción al hacer clic
                callback: () => {
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },

                // IMPORTANTE: Esto le dice a Odoo "Muéstralo siempre"
                isAvailable: () => true,
                sequence: 1,
            };
        }

        return items;
    }
});