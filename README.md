# Validador de inventario desde CSV

Herramienta de terminal para revisar un archivo de inventario antes de importarlo. Detecta SKU repetidos, campos obligatorios vacíos y cantidades inválidas. Genera un reporte Markdown con los registros que necesitan corrección.

## Ejecutar la demo

Necesitas Python 3.10 o posterior. El proyecto usa la biblioteca estándar de Python.

```bash
git clone https://github.com/Jonath93/ValidadorCVE.git
cd ValidadorCVE
python validar_inventario.py ejemplos/inventario_con_errores.csv --reporte reporte.md
```

En Windows, si usas el lanzador de Python, sustituye `python` por `py`.

Abre `reporte.md`. El ejemplo genera cuatro infracciones en cuatro registros:

| Registro | Campo | Código | Qué corregir |
| --- | --- | --- | --- |
| 2 | sku | SKU_DUPLICADO | Usa un SKU único para cada producto. |
| 3 | sku | SKU_DUPLICADO | Usa un SKU único para cada producto. |
| 4 | cantidad | CANTIDAD_INVALIDA | Escribe un número entero mayor o igual a cero. |
| 5 | nombre | NOMBRE_REQUERIDO | Escribe el nombre del producto. |

Ejecuta el mismo flujo con el archivo corregido:

```bash
python validar_inventario.py ejemplos/inventario_valido.csv --reporte reporte_valido.md
```

El segundo reporte indica que los cuatro registros son válidos.

## Formato y reglas

- El CSV debe estar en UTF-8, con comas y encabezados `sku`, `nombre` y `cantidad`. Se aceptan columnas adicionales y cualquier orden de los encabezados.
- El SKU y el nombre son obligatorios. El programa recorta espacios al comparar SKU y distingue mayúsculas de minúsculas.
- Si un SKU se repite, aparecen todos los registros involucrados. El programa cuenta primero cuántas veces aparece cada SKU y después valida los registros en su orden original.
- La cantidad admite dígitos del 0 al 9. Por ejemplo, `0` y `002` son válidos.
- El número del reporte identifica el registro del CSV contando el encabezado como registro 1. Un campo entre comillas puede abarcar varias líneas y sigue contando como un solo registro.

| Código de salida | Significado |
| --- | --- |
| `0` | Archivo válido. |
| `1` | Se generó el reporte con infracciones. |
| `2` | Error al leer el CSV o al escribir el reporte. |

El programa abre el inventario en modo lectura. La ruta indicada en `--reporte` puede ser la de un reporte previo.

## Pruebas y especificación

```bash
python -m unittest discover -s tests
```

[PROPUESTA.md](PROPUESTA.md) documenta el alcance y los criterios de aceptación. Un asistente como Claude Code o Codex puede leer esa especificación para revisar el código o leer un reporte generado para explicar los hallazgos.
