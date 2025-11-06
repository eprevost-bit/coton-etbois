import { SaleOrderLineProductField } from "@sale/js/sale_product_field";
import { patch } from "@web/core/utils/patch";
import { useState, onWillStart } from "@odoo/owl"; // <-- Añade 'onWillStart'

patch(SaleOrderLineProductField.prototype, {
    setup() {
        super.setup(...arguments);

        this.state = useState({
            count_item_under_section: 0,
        });

        // *** AÑADE ESTO ***
        // Llama a la función de conteo ANTES de que el componente se renderice

    },

    async countItemUnderSection () {
        // Esta función ahora solo es llamada una vez por onWillStart
        await this.env.bus.trigger("count_item_under_section", {
            state: this.state,
            record: this.props.record
        });
    },
});