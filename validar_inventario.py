"""Valida un inventario CSV y genera un reporte Markdown."""

import argparse
import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

CAMPOS = ("sku", "nombre", "cantidad")
CANTIDAD = re.compile(r"[0-9]+")


class ErrorEntrada(ValueError):
    """El archivo no tiene una estructura que se pueda validar."""


@dataclass(frozen=True)
class Registro:
    numero: int
    sku: str
    nombre: str
    cantidad: str


@dataclass(frozen=True)
class Infraccion:
    registro: int
    campo: str
    codigo: str
    mensaje: str


def leer_inventario(ruta: Path) -> list[Registro]:
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.reader(archivo, strict=True)
        filas = (fila for fila in lector if fila)
        encabezados = [campo.strip() for campo in next(filas, [])]
        if len(set(encabezados)) != len(encabezados):
            raise ErrorEntrada("Hay encabezados repetidos.")
        faltantes = [campo for campo in CAMPOS if campo not in encabezados]
        if faltantes:
            raise ErrorEntrada(f"Faltan columnas requeridas: {', '.join(faltantes)}.")

        indices = [encabezados.index(campo) for campo in CAMPOS]
        registros = []
        for numero, fila in enumerate(filas, start=2):
            if len(fila) != len(encabezados):
                raise ErrorEntrada(
                    f"El registro {numero} tiene {len(fila)} columnas. "
                    f"Se esperaban {len(encabezados)}."
                )
            sku, nombre, cantidad = (fila[indice].strip() for indice in indices)
            registros.append(Registro(numero, sku, nombre, cantidad))

    if not registros:
        raise ErrorEntrada("El archivo debe incluir al menos un registro de inventario.")
    return registros


def validar(registros: list[Registro]) -> list[Infraccion]:
    frecuencia_sku = Counter(registro.sku for registro in registros if registro.sku)
    infracciones = []
    for registro in registros:
        numero = registro.numero
        if not registro.sku:
            infracciones.append(Infraccion(
                numero, "sku", "SKU_REQUERIDO", "Escribe el SKU del producto."
            ))
        elif frecuencia_sku[registro.sku] > 1:
            infracciones.append(Infraccion(
                numero, "sku", "SKU_DUPLICADO", "Usa un SKU único para cada producto."
            ))
        if not registro.nombre:
            infracciones.append(Infraccion(
                numero, "nombre", "NOMBRE_REQUERIDO", "Escribe el nombre del producto."
            ))
        if not CANTIDAD.fullmatch(registro.cantidad):
            infracciones.append(Infraccion(
                numero, "cantidad", "CANTIDAD_INVALIDA",
                "Escribe un número entero mayor o igual a cero."
            ))
    return infracciones


def crear_reporte(total_registros: int, infracciones: list[Infraccion]) -> str:
    registros_con_errores = {infraccion.registro for infraccion in infracciones}
    resultado = "Con errores" if infracciones else "Válido"
    lineas = [
        "# Validación de inventario",
        "",
        f"**Resultado** {resultado}",
        "",
        f"- Registros revisados: {total_registros}",
        f"- Registros con errores: {len(registros_con_errores)}",
        f"- Infracciones: {len(infracciones)}",
    ]
    if infracciones:
        lineas += [
            "",
            "| Registro | Campo | Código | Qué corregir |",
            "| --- | --- | --- | --- |",
        ]
        lineas.extend(
            f"| {item.registro} | {item.campo} | {item.codigo} | {item.mensaje} |"
            for item in infracciones
        )
    return "\n".join(lineas) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", type=Path, help="Archivo CSV de inventario")
    parser.add_argument("--reporte", type=Path, required=True, help="Ruta del reporte Markdown")
    args = parser.parse_args()

    try:
        misma_ruta = args.archivo.resolve() == args.reporte.resolve()
        mismo_archivo = (
            args.archivo.exists() and args.reporte.exists()
            and args.archivo.samefile(args.reporte)
        )
    except (OSError, RuntimeError):
        print("No se pudieron comprobar las rutas de entrada y reporte.", file=sys.stderr)
        return 2
    if misma_ruta or mismo_archivo:
        print("Usa una ruta de reporte distinta del archivo de inventario.", file=sys.stderr)
        return 2

    error = None
    try:
        registros = leer_inventario(args.archivo)
    except ErrorEntrada as exc:
        error = str(exc)
    except UnicodeError:
        error = "El CSV debe estar codificado en UTF-8."
    except csv.Error:
        error = "El archivo contiene un CSV mal formado."
    except FileNotFoundError:
        error = "No se encontró el archivo CSV."
    except OSError:
        error = "No se pudo leer el archivo CSV."

    if error is None:
        infracciones = validar(registros)
        reporte = crear_reporte(len(registros), infracciones)
        codigo = 1 if infracciones else 0
    else:
        print(error, file=sys.stderr)
        reporte = f"# Validación de inventario\n\n**Resultado** Error de entrada\n\n{error}\n"
        codigo = 2

    try:
        args.reporte.write_text(reporte, encoding="utf-8")
    except OSError:
        print("No se pudo escribir el reporte. Revisa la ruta y los permisos.", file=sys.stderr)
        return 2
    print(f"Reporte generado en {args.reporte}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
