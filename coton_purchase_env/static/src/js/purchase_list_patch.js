/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

console.log("✅ EL PARCHE SE HA CARGADO EN MEMORIA (V2)");

patch(ListController.prototype, {
    setup() {
        super.setup();
        // ESTO NOS DIRÁ CÓMO SE LLAMAN AHORA LAS FUNCIONES
        console.log("🕵️‍♂️ MÉTODOS DISPONIBLES:", Object.getOwnPropertyNames(ListController.prototype));
        console.log("🕵️‍♂️ PROPIEDADES EN SETUP:", Object.keys(this));
    }
});

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
        // 1. Obtenemos los ítems originales (Importar, Exportar, etc.)
        const items = super.getStaticActionMenuItems();

        // 2. Verificamos si estamos en Compras
        if (this.props.resModel === 'purchase.order') {

            // 3. Añadimos nuestro botón al final
            items.push({
                key: "import_excel_custom", // Importante ponerle una key única
                description: "📥 Importar Precios (Excel)",
                callback: () => {
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },
            });
        }

        return items;
    }
});