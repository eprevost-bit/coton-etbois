/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
        console.log("👻 SETUP OK: El parche está listo en Compras.");
    },

    // ESTRATEGIA: Interceptamos AMBOS menús posibles
    get cogItems() {
        const items = super.cogItems || [];

        if (this.props.resModel === 'purchase.order') {
            console.log("⚙️ Intentando inyectar en cogItems (Array)...");

            // Creamos un item compatible con Odoo 18
            const myItem = {
                name: "import_excel_global",
                description: "📥 Importar Precios (Excel)",
                action: () => {
                    console.log("🚀 EJECUTANDO ACCIÓN");
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },
                sequence: 1 // Forzamos que salga arriba
            };

            // Usamos spread para asegurar reactividad (truco de OWL)
            return [...items, myItem];
        }
        return items;
    },

    getStaticActionMenuItems() {
        const items = super.getStaticActionMenuItems();

        if (this.props.resModel === 'purchase.order') {
             // Si items es un Objeto (que lo es), le metemos la clave
             if (!items.custom_excel_import) {
                 items.custom_excel_import = {
                    description: "📥 Importar Precios (Excel)",
                    isAvailable: () => true, // ¡IMPORTANTE! Forzar que se vea sin selección
                    callback: () => {
                        this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                    },
                    sequence: 1
                 };
             }
        }
        return items;
    }
});