# Validador de inventario desde CSV

## Objetivo

Construir una herramienta de línea de comandos que revise un archivo de inventario antes de importarlo. La persona que usa la herramienta debe poder saber si el archivo pasa la validación, qué registros debe corregir y por qué.

Esta especificación está dirigida a Claude Code o Codex para implementar el proyecto. El programa aplica las reglas con código Python y genera un segundo archivo Markdown, `reporte.md`, que la persona o un asistente pueden leer para revisar los hallazgos. El programa funciona localmente y sin servicios externos.

## Primera versión

Usa Python y su biblioteca estándar. El comando de entrada debe ser:

```bash
python validar_inventario.py inventario.csv --reporte reporte.md
```

Lee un CSV separado por comas con encabezados `sku`, `nombre` y `cantidad`. Acepta UTF-8 con o sin BOM, columnas adicionales y cualquier orden de las columnas requeridas. Los encabezados se comparan con los nombres indicados después de recortar espacios. Un encabezado ausente o repetido, un registro con un número incorrecto de columnas o un CSV mal formado es un error de entrada. Un CSV con encabezados y sin registros también es un error de entrada.

### Reglas por registro

| Código | Campo | Regla |
| --- | --- | --- |
| `SKU_REQUERIDO` | `sku` | El valor debe contener texto después de recortar espacios. |
| `SKU_DUPLICADO` | `sku` | Un SKU aparece una sola vez. Compara después de recortar espacios y conserva la distinción entre mayúsculas y minúsculas. Si se repite, marca todos los registros involucrados. Los SKU vacíos se reportan solo como obligatorios. |
| `NOMBRE_REQUERIDO` | `nombre` | El valor debe contener texto después de recortar espacios. |
| `CANTIDAD_INVALIDA` | `cantidad` | Después de recortar espacios, debe contener uno o más dígitos del 0 al 9. `0` y `002` son válidos. Los valores vacíos, negativos, decimales y con texto son inválidos. |

Reporta todas las infracciones de datos que encuentres. Identifica cada registro con su posición en el CSV, contando el encabezado como registro 1 e ignorando líneas vacías fuera de un registro. Un campo entre comillas que ocupa varias líneas sigue perteneciendo a un solo registro. Conserva el orden de los registros y, dentro de cada registro, el orden de la tabla de reglas.

### Reporte y resultado del comando

Genera un reporte Markdown con el resultado general, el número de registros revisados, el número de registros con errores, el total de infracciones y una tabla con registro, campo, código y explicación. Una fila con dos infracciones cuenta como un registro con errores. Usa mensajes en español y explica qué corregir. Si el archivo no se puede leer o su estructura es inválida, genera un reporte con el motivo y sin una tabla de validación parcial, siempre que sea posible escribir el reporte.

| Código de salida | Resultado |
| --- | --- |
| `0` | Archivo válido y reporte generado. |
| `1` | Archivo legible con infracciones de datos y reporte generado. |
| `2` | Error de entrada o de escritura del reporte. Muestra el motivo por la salida de errores. |

Abre el CSV solo para lectura. Rechaza una ruta de reporte que apunte al archivo de entrada para evitar sobrescribir el inventario. Una ejecución normal puede reemplazar un reporte anterior en la ruta indicada.

## Ejemplo para la demo

```csv
sku,nombre,cantidad
A01,Tornillos,10
A01,Tuercas,3
B02,Arandelas,-2
C03,,0
```

Resultado esperado para `reporte.md`:

```md
# Validación de inventario

**Resultado** Con errores

- Registros revisados: 4
- Registros con errores: 4
- Infracciones: 4

| Registro | Campo | Código | Qué corregir |
| --- | --- | --- | --- |
| 2 | sku | SKU_DUPLICADO | Usa un SKU único para cada producto. |
| 3 | sku | SKU_DUPLICADO | Usa un SKU único para cada producto. |
| 4 | cantidad | CANTIDAD_INVALIDA | Escribe un número entero mayor o igual a cero. |
| 5 | nombre | NOMBRE_REQUERIDO | Escribe el nombre del producto. |
```

El comando termina con código `1`. Para la segunda parte de la demo, cambia el segundo SKU a `A02`, la cantidad negativa a `2` y el nombre vacío a `Clavos`. La misma ejecución debe generar un reporte válido con cuatro registros revisados, cero infracciones y código `0`.

## Entrega y verificación

1. Revisa el proyecto de destino y respeta sus convenciones. Si está vacío, crea `validar_inventario.py`, `tests/test_validar_inventario.py`, dos CSV de ejemplo en `ejemplos/` y un `README.md`.
2. Mantén las reglas de validación separadas de la lectura de archivos y de la escritura del reporte para poder probarlas directamente.
3. Cubre con pruebas el archivo válido, ambos registros de un SKU duplicado, varias infracciones en un mismo registro, campos vacíos, cantidades inválidas, encabezados faltantes y un campo con comillas que contenga una coma. Verifica también los tres códigos de salida desde el comando.
4. Ejecuta `python -m unittest discover -s tests` y prueba el comando con los dos archivos de ejemplo. En el README explica el problema, cómo reproducir la demo y cómo interpretar el reporte. Incluye una muestra del reporte con errores.

La primera versión se limita al comando local, el reporte y sus pruebas. Una interfaz web o reglas configurables pueden ser iteraciones posteriores.
