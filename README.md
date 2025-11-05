# Módulo Personalizado: Coton et Bois para Odoo 18-19

## Descripción General

Este módulo introduce personalizaciones y nuevas funcionalidades a los flujos de Compras y Ventas de Odoo 18 - 19, diseñadas para optimizar los procesos específicos de "Coton et Bois".

Las principales mejoras se centran en la capacidad de gestionar presupuestos de compra complejos y en añadir un nivel de detalle granular a las líneas de los pedidos de venta.

## Características Principales

### 1. Gestión de Compras Avanzada

-   **Generación de Múltiples Pedidos de Compra**: Permite crear un presupuesto de compra inicial y, con un solo clic, generar automáticamente múltiples pedidos de compra, agrupando los productos por el proveedor asignado en cada línea.
-   **Asignación de Proveedor por Línea**: Se ha añadido un campo "Proveedor" en cada línea del pedido de compra para facilitar la funcionalidad anterior.
-   **Nuevo Estado "Presupuesto Inicial"**: El presupuesto original que se utiliza para generar los demás queda en un estado informativo llamado `Presupuesto Inicial`, manteniendo un registro claro del origen.
-   **Flujo de Estados Simplificado**: Se han eliminado los estados `RFQ Enviado` e `Intermedio` para adaptar el flujo a un proceso más directo.

### 2. Gestión de Ventas con Subsecciones

-   **Desglose de Líneas de Venta**: Permite desglosar una única línea de pedido de venta en múltiples "subsecciones" o componentes.
-   **Cálculo Automático de Precios**: El precio de la línea de venta principal se calcula automáticamente como la suma de los subtotales de sus subsecciones. El campo de precio se bloquea para evitar inconsistencias.
-   **Interfaz Integrada**: Las subsecciones se gestionan directamente desde la línea del pedido de venta a través de una tabla editable, haciendo el proceso rápido e intuitivo.

## Instalación

1.  Asegúrate de que esta carpeta (`coton-etbois`) se encuentre en tu directorio de addons personalizados de Odoo.
2.  Reinicia el servicio de Odoo.
3.  Activa el modo desarrollador en Odoo.
4.  Ve al menú de `Aplicaciones`.
5.  Haz clic en `Actualizar lista de aplicaciones`.
6.  Busca "Coton et Bois" en la barra de búsqueda y haz clic en **Instalar**.

## Guía de Uso

### ¿Cómo generar múltiples pedidos de compra?

1.  Ve al módulo de **Compras** y crea un nuevo "Pedido de Compra".
2.  Añade los productos que necesites en las líneas del pedido.
3.  En cada línea, utiliza el nuevo campo **"Proveedor"** para asignar el proveedor al que deseas comprar ese artículo específico. Puedes tener diferentes proveedores en distintas líneas.
4.  Una vez que hayas configurado todas las líneas con sus respectivos proveedores, guarda el presupuesto.
5.  Haz clic en el botón **"Establecer como Presupuesto Inicial"**.
6.  **Resultado**:
    -   El presupuesto actual cambiará al estado `Presupuesto Inicial`.
    -   Se crearán automáticamente nuevos Pedidos de Compra (en estado `Borrador`), uno por cada proveedor que hayas asignado en las líneas.
    -   Serás redirigido a una lista con los nuevos pedidos generados.

### ¿Cómo usar las subsecciones en un pedido de venta?

1.  Ve al módulo de **Ventas** y crea un nuevo "Pedido de Venta".
2.  Añade un producto en una línea de pedido como lo harías normalmente.
3.  Debajo de la descripción del producto en esa línea, verás una nueva tabla para **Subsecciones**.
4.  Haz clic en **"Añadir una línea"** dentro de esa tabla para empezar a desglosar el producto principal. Puedes añadir productos, descripciones, cantidades y precios para cada subsección.
5.  **Resultado**:
    -   A medida que añadas o modifiques las subsecciones, el campo **"Precio Unitario"** de la línea de venta principal se actualizará automáticamente con la suma total de las subsecciones.
    -   Este campo de precio principal se volverá de solo lectura para garantizar que el total siempre coincida con el desglose.

## Dependencias

Este módulo depende de los siguientes módulos estándar de Odoo:
-   `purchase`
-   `sale_management`

---
Desarrollado por: **[ernestopr@unlimioo.com/Unlimioo]**
