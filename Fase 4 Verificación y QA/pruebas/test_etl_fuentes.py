import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from openpyxl import Workbook

from sgma.errores import RegistroErrores
from sgma.etl import transformar_actas, transformar_alumnos, transformar_plan


class FuentesETLTests(unittest.TestCase):
    def setUp(self):
        self.temporal = TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.raiz = Path(self.temporal.name)

    def _excel(self, nombre, hoja, encabezados, filas):
        libro = Workbook()
        ws = libro.active
        ws.title = hoja
        ws.append(encabezados)
        for fila in filas:
            ws.append(fila)
        ruta = self.raiz / nombre
        libro.save(ruta)
        libro.close()
        return ruta

    def _fuentes(self):
        plan = self._excel(
            "Plan_Estudios.xlsx",
            "Materias",
            ["Nom_Carrera", "Cod_Mat", "Nombre_Materia", "Año_Cursada"],
            [["Sistemas", "SIS-101", "Introducción", "1°"]],
        )
        alumnos = self._excel(
            "Alumnos_2026_Final.xlsx",
            "Hoja1",
            ["Documento", "Nombre_Y_Apellido", "Fecha_Nac", "E-mail", "Legajo_Old"],
            [[12345678, "Pérez, Ana", date(2000, 1, 2), "ana@example.edu", 100]],
        )
        actas = self.raiz / "Actas_Historicas.csv"
        actas.write_text(
            "DNI_Alumno,Cod_Materia,Fecha_Examen,Condición,Nota_Final,Libro_Folio\n"
            "12345678,SIS101,2024-06-10,APROBADO,8,1-1\n",
            encoding="utf-8-sig",
        )
        return alumnos, plan, actas

    def test_plan_de_estudios_produce_codigos_unicos_y_anios_validos(self):
        errores = RegistroErrores()
        _, plan, _ = self._fuentes()
        carreras, materias = transformar_plan(plan, errores)
        self.assertTrue(carreras)
        self.assertTrue(materias)
        codigos = [materia["codigo"] for materia in materias]
        self.assertEqual(len(codigos), len(set(codigos)))
        self.assertTrue(all(1 <= materia["anio_nivel"] <= 5 for materia in materias))

    def test_alumnos_normalizados_no_repiten_dni_ni_legajo(self):
        alumnos, _, _ = self._fuentes()
        filas = transformar_alumnos(alumnos, RegistroErrores())
        self.assertTrue(filas)
        self.assertEqual(len({fila["dni"] for fila in filas}), len(filas))
        self.assertEqual(len({fila["legajo"] for fila in filas}), len(filas))
        self.assertTrue(all(fila["dni"].isdigit() for fila in filas))
        self.assertTrue(all(len(fila["nombre"]) <= 50 and len(fila["apellido"]) <= 50 for fila in filas))

    def test_actas_solo_conserva_referencias_y_fechas_validas(self):
        errores = RegistroErrores()
        archivo_alumnos, archivo_plan, archivo_actas = self._fuentes()
        alumnos = transformar_alumnos(archivo_alumnos, errores)
        carreras, materias = transformar_plan(archivo_plan, errores)
        actas = transformar_actas(
            archivo_actas,
            {fila["dni"] for fila in alumnos},
            {fila["codigo"] for fila in materias},
            errores,
        )
        self.assertTrue(actas)
        self.assertTrue(all(acta["dni"] in {fila["dni"] for fila in alumnos} for acta in actas))
        self.assertTrue(all(acta["codigo_materia"] in {fila["codigo"] for fila in materias} for acta in actas))
        self.assertTrue(all(acta["fecha_examen"] <= date.today() for acta in actas))
        self.assertTrue(all(acta["nota"] is None if acta["estado"] == "AUSENTE" else acta["nota"] is not None for acta in actas))


if __name__ == "__main__":
    unittest.main()
