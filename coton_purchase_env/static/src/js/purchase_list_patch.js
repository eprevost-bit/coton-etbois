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

    // AQUI ESTÁ LA CLAVE: Usamos 'cogItems' para la tuerca global
    get cogItems() {
        const items = super.cogItems;

        // 2. DIAGNÓSTICO: Para que confirmes que AHORA SÍ es el menú correcto
        console.log("⚙️ TUERCA GLOBAL ITEMS:", items);

        // 3. Verificamos modelo
        if (this.props.resModel === 'purchase.order') {

            // 4. Agregamos tu botón a la lista
            items.push({
                name: "import_excel_global_btn",
                description: "📥 Importar Precios (Excel)",
                // Esta función se ejecuta al dar clic
                action: () => {
                    console.log("🚀 Abriendo Wizard Global...");
                    this.actionService.doAction("coton-etbois.action_purchase_import_wizard_global");
                },
                sequence: 10, // Puedes jugar con esto para subirlo o bajarlo
            });
        }

        return items;
    }
});