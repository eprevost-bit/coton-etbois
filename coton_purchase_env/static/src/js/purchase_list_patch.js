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
        // ESTO DEBE SALIR AL REFRESCAR LA PÁGINA (sin tocar nada)
        console.log("👻 LIST CONTROLLER INICIADO. Modelo:", this.props.resModel);
    },

    get cogItems() {
        const items = super.cogItems;
        console.log("👉 CLICK EN TUERCA DETECTADO en modelo:", this.props.resModel);

        if (this.props.resModel === 'purchase.order') {
            items.push({
                name: "import_excel_global",
                description: "📥 Importar Precios (Excel)",
                action: () => {
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },
            });
        }
        return items;
    }
});