/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

console.log("✅ EL PARCHE SE HA CARGADO EN MEMORIA");

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.actionService = useService("action");
    },

    get cogItems() {
        // 1. Obtenemos los ítems originales de la tuerca
        const items = super.cogItems;

        // 2. IMPRIMIR EN CONSOLA QUÉ ESTÁ VIENDO ODOO
        console.log("👉 ABRIENDO TUERCA. MODELO DETECTADO:", this.props.resModel);

        // 3. Verificamos si coincide con 'purchase.order'
        if (this.props.resModel === 'purchase.order') {
            console.log("🟢 ¡COINCIDENCIA! AGREGANDO BOTÓN AL MENÚ...");

            items.push({
                name: "import_excel_global",
                description: "📥 Importar Precios (Excel)",
                action: () => {
                    console.log("🚀 EJECUTANDO ACCIÓN DE IMPORTAR");
                    // Asegúrate de que 'coton-etbois' sea el nombre real de tu carpeta técnica
                    this.actionService.doAction("coton_purchase_env.action_purchase_import_wizard_global");
                },
            });
        } else {
            console.log("🔴 EL BOTÓN NO SE AGREGA PORQUE EL MODELO NO ES 'purchase.order'");
        }

        return items;
    }
});