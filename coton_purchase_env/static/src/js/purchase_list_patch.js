/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

// Solo un patch, limpio y ordenado
patch(ListController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
        console.log("👻 SETUP INICIADO: El parche está activo en esta vista.");
    },

    get cogItems() {
        // Obtenemos la lista original
        const items = super.cogItems || [];

        // LOG CLAVE: Esto saldrá AL REFRESCAR LA PÁGINA (F5), no al dar clic
        console.log("⚙️ CARGANDO ITEMS DE LA TUERCA. Cantidad actual:", items.length);

        if (this.props.resModel === 'purchase.order') {

            // Agregamos el botón con TODAS las variantes posibles para asegurar compatibilidad
            items.push({
                key: "import_excel_global_btn",
                name: "Importar Excel Personalizado",
                description: "📥 Importar Precios (Excel)", // Texto visible
                label: "📥 Importar Precios (Excel)",       // Texto visible alternativo

                // Ponemos los 3 métodos para que uno "muerda" el anzuelo
                action: () => {
                    console.log("🚀 EJECUTANDO ACCIÓN (vía action)");
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },
                callback: () => {
                    console.log("🚀 EJECUTANDO ACCIÓN (vía callback)");
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },
                onClick: () => {
                    console.log("🚀 EJECUTANDO ACCIÓN (vía onClick)");
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },

                sequence: 1, // Intentamos ponerlo EL PRIMERO para verlo fácil
            });

            console.log("✅ BOTÓN INYECTADO EN LA LISTA.");
        }

        return items;
    }
});