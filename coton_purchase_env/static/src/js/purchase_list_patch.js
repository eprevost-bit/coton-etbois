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

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
    },

    getStaticActionMenuItems() {
        // 1. Obtenemos el objeto original de items
        const items = super.getStaticActionMenuItems();

        // 2. DIAGNÓSTICO: Esto te mostrará en la consola qué es exactamente "items"
        // Verás que es algo como { export: {...}, import: {...} }
        console.log("🕵️‍♂️ EL OBJETO SECRETOS DE ITEMS ES:", items);

        // 3. Verificamos que estamos en Compras
        if (this.props.resModel === 'purchase.order') {

            // 4. CORRECCIÓN: No usamos .push().
            // Añadimos una nueva propiedad al objeto directamente.
            items.import_excel_custom = {
                description: "📥 Importar Precios (Excel)",
                callback: () => {
                    console.log("🚀 Ejecutando acción de importar...");
                    // Asegúrate de que este ID sea correcto en tu XML
                    this.actionService.doAction("coton-etbois.action_purchase_import_wizard_global");
                },
                sequence: 50, // Intentamos ponerlo al final
            };
        }

        return items;
    }
});