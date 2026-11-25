import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validar_inventario import ErrorEntrada, Registro, crear_reporte, leer_inventario, validar

RAIZ = Path(__file__).resolve().parents[1]


class ValidadorTest(unittest.TestCase):
    def setUp(self):
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        self.ruta = Path(carpeta.name)
        self.csv = self.ruta / "inventario.csv"
        self.reporte = self.ruta / "reporte.md"

    def ejecutar(self, archivo, reporte):
        return subprocess.run(
            [sys.executable, str(RAIZ / "validar_inventario.py"),
             str(archivo), "--reporte", str(reporte)],
            capture_output=True,
        )

    def test_archivo_valido_con_bom_columnas_reordenadas_y_comillas(self):
        self.csv.write_text(
            '\ncantidad,nota, sku ,nombre\n002,extra, A01 ,"Tornillos, grandes"\n'
            '\n0,extra,a01,"Clavos\nmedianos"\n',
            encoding="utf-8-sig", newline="",
        )
        registros = leer_inventario(self.csv)
        self.assertEqual(registros, [
            Registro(2, "A01", "Tornillos, grandes", "002"),
            Registro(3, "a01", "Clavos\nmedianos", "0"),
        ])
        self.assertEqual(validar(registros), [])

    def test_marca_ambos_sku_duplicados_y_ordena_infracciones(self):
        registros = [
            Registro(2, "A01", "", "-2"),
            Registro(3, "A01", "Clavos", "0"),
            Registro(4, "", "", ""),
            Registro(5, "", "Clavos", "1"),
        ]
        infracciones = validar(registros)
        self.assertEqual([(item.registro, item.codigo) for item in infracciones], [
            (2, "SKU_DUPLICADO"),
            (2, "NOMBRE_REQUERIDO"),
            (2, "CANTIDAD_INVALIDA"),
            (3, "SKU_DUPLICADO"),
            (4, "SKU_REQUERIDO"),
            (4, "NOMBRE_REQUERIDO"),
            (4, "CANTIDAD_INVALIDA"),
            (5, "SKU_REQUERIDO"),
        ])
        reporte = crear_reporte(len(registros), infracciones)
        self.assertIn("Registros con errores: 4", reporte)
        self.assertIn("Infracciones: 8", reporte)

    def test_cantidades_invalidas(self):
        for cantidad in ("-1", "1.0", "+1", "dos", "١", ""):
            with self.subTest(cantidad=cantidad):
                resultado = validar([Registro(2, "A01", "Clavos", cantidad)])
                self.assertEqual([item.codigo for item in resultado], ["CANTIDAD_INVALIDA"])

    def test_errores_de_estructura(self):
        casos = (
            ("sku,nombre\nA01,Clavos\n", "Faltan columnas"),
            ("sku,nombre,cantidad, sku \nA01,Clavos,1,A01\n", "encabezados repetidos"),
            ("sku,nombre,cantidad\nA01,Clavos\n", "registro 2"),
            ("sku,nombre,cantidad\n", "al menos un registro"),
        )
        for contenido, mensaje in casos:
            with self.subTest(mensaje=mensaje):
                self.csv.write_text(contenido, encoding="utf-8")
                with self.assertRaisesRegex(ErrorEntrada, mensaje):
                    leer_inventario(self.csv)

    def test_comando_con_los_dos_ejemplos(self):
        casos = (
            ("inventario_valido.csv", 0, "0"),
            ("inventario_con_errores.csv", 1, "4"),
        )
        for archivo, codigo, total in casos:
            with self.subTest(archivo=archivo):
                resultado = self.ejecutar(RAIZ / "ejemplos" / archivo, self.reporte)
                self.assertEqual(resultado.returncode, codigo, resultado.stderr)
                self.assertIn(
                    f"Infracciones: {total}", self.reporte.read_text(encoding="utf-8")
                )

    def test_csv_mal_formado_genera_reporte_de_entrada(self):
        self.csv.write_text('sku,nombre,cantidad\nA01,"Clavos,1\n', encoding="utf-8")
        resultado = self.ejecutar(self.csv, self.reporte)
        self.assertEqual(resultado.returncode, 2)
        self.assertIn(b"CSV mal formado", resultado.stderr)
        reporte = self.reporte.read_text(encoding="utf-8")
        self.assertIn("Error de entrada", reporte)
        self.assertNotIn("| Registro |", reporte)

    def test_comando_rechaza_sobrescribir_el_csv(self):
        contenido = b"sku,nombre,cantidad\nA01,Clavos,0\n"
        self.csv.write_bytes(contenido)
        resultado = self.ejecutar(self.csv, self.csv)
        self.assertEqual(resultado.returncode, 2)
        self.assertEqual(self.csv.read_bytes(), contenido)

    def test_error_al_escribir_el_reporte(self):
        resultado = self.ejecutar(RAIZ / "ejemplos" / "inventario_valido.csv", self.ruta)
        self.assertEqual(resultado.returncode, 2)
        self.assertIn(b"No se pudo escribir el reporte", resultado.stderr)


if __name__ == "__main__":
    unittest.main()
