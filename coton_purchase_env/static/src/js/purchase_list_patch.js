/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
    },

    // ESTE ES EL NOMBRE CORRECTO PARA LA TUERCA GLOBAL
    get cogItems() {
        // 1. Obtenemos la lista existente (debe ser un Array [])
        const items = super.cogItems;

        // 2. LOG: Si ves esto en consola, ESTAMOS EN EL SITIO CORRECTO
        console.log("⚙️ ENTRANDO EN TUERCA GLOBAL (cogItems). Items actuales:", items);

        // 3. Verificamos modelo
        if (this.props.resModel === 'purchase.order') {

            // 4. Inyectamos tu botón
            // En 'cogItems', items SI es un Array, así que .push funciona perfecto.
            items.push({
                name: "import_excel_global_custom",
                description: "📥 Importar Precios (Excel)",

                // En la tuerca global, la función se llama 'action'
                action: () => {
                    console.log("🚀 Click en Importar Global");
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },

                sequence: 1, // Intentamos ponerlo el primero
            });
        }

        return items;
    }
});