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

    get cogItems() {
        const items = super.cogItems;

        // --- EL CHIVATO ---
        // Esto imprimirá en la consola cómo está hecho el primer botón (ej. "Exportar")
        // Así sabremos si usa "name", "label", "description", "callback", etc.
        if (items.length > 0) {
            console.log("🔍 ESTRUCTURA DE UN BOTÓN REAL:", items[0]);
            console.log("🔑 LLAVES QUE USA:", Object.keys(items[0]));
        }
        // ------------------

        if (this.props.resModel === 'purchase.order') {

            // INTENTO DE SOLUCIÓN: Usamos 'callback' y duplicamos etiquetas por seguridad
            items.push({
                name: "import_excel_global",       // Identificador interno
                description: "📥 Importar Precios (Excel)", // Usado en algunos menús
                label: "📥 Importar Precios (Excel)",       // Usado en otros menús (por si acaso)
                title: "📥 Importar Precios (Excel)",       // Otra variante posible

                // CAMBIO CLAVE: Usamos 'callback' en lugar de 'action'
                callback: () => {
                    console.log("🚀 Click recibido");
                    this.actionService.doAction("coton-etbois.action_purchase_import_wizard_global");
                },

                sequence: 100, // Lo mandamos al final
            });
        }

        return items;
    }
});