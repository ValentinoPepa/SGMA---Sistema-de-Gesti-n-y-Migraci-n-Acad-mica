import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook

os.environ.setdefault("SGMA_SECRET_KEY", "clave-temporal-para-pruebas")
import sgma.web as web


class CursorUsuario:
    def __init__(self, rol="ADMIN", callproc_result=None):
        self.rol = rol
        self.ultima_consulta = ""
        self.consultas = []
        self.parametros = []
        self.lastrowid = 1
        self.callproc_result = callproc_result if callproc_result is not None else (1200,)

    def execute(self, consulta, parametros=None):
        self.ultima_consulta = consulta
        self.consultas.append(consulta)
        self.parametros.append(parametros)
        if consulta.lstrip().upper().startswith("INSERT INTO"):
            self.lastrowid += 1

    def fetchone(self):
        consulta = self.ultima_consulta.lower()
        if "from usuarios u join roles" in consulta:
            return {"id_usuario": 7, "username": "qa", "id_rol": 1, "rol": self.rol}
        if "select id_carrera" in consulta:
            return {"id_carrera": 4}
        return None

    def callproc(self, _nombre, _parametros):
        return self.callproc_result

    def fetchall(self):
        return []

    def close(self):
        pass


class PermisosYCargaTests(unittest.TestCase):
    def crear_cliente(self, rol="ADMIN"):
        cliente = web.app.test_client()
        sesion = cliente.session_transaction()
        with sesion as valores:
            valores["usuario_id"] = 7
            valores["csrf"] = "token-prueba"
        return cliente, patch.object(web, "_cursor", return_value=CursorUsuario(rol))

    def test_usuarios_requiere_sesion(self):
        respuesta = web.app.test_client().get("/usuarios")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/login", respuesta.location)

    def test_preceptor_no_accede_a_administracion_de_usuarios(self):
        cliente, parche = self.crear_cliente("PRECEPTOR")
        with parche:
            respuesta = cliente.get("/usuarios")
        self.assertEqual(respuesta.status_code, 403)

    def test_administrador_accede_a_administracion_de_usuarios(self):
        cliente, _ = self.crear_cliente("ADMIN")
        with patch.object(web, "_cursor", return_value=CursorUsuario("ADMIN")):
            respuesta = cliente.get("/usuarios")
        self.assertEqual(respuesta.status_code, 200)

    def test_inicio_muestra_bienvenida_y_accesos_directos(self):
        cliente, _ = self.crear_cliente("ADMIN")
        with patch.object(web, "_cursor", return_value=CursorUsuario("ADMIN")):
            respuesta = cliente.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Accesos directos".encode(), respuesta.data)
        self.assertIn("Asistencias".encode(), respuesta.data)

    def test_asistencias_muestra_detalle_por_fecha(self):
        cliente, _ = self.crear_cliente("ADMIN")
        cursor = CursorUsuario("ADMIN")
        with patch.object(web, "_cursor", return_value=cursor):
            respuesta = cliente.get("/asistencias")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Detalle por fecha".encode(), respuesta.data)
        self.assertIn("Todavía no hay asistencias cargadas.".encode(), respuesta.data)

    def test_directivo_no_puede_crear_alumnos(self):
        cliente, _ = self.crear_cliente("DIRECTIVO")
        with patch.object(web, "_cursor", return_value=CursorUsuario("DIRECTIVO")):
            respuesta = cliente.post("/alumnos", data={"accion": "crear"})
        self.assertEqual(respuesta.status_code, 403)

    def test_alta_alumno_acepta_legajo_out_como_diccionario(self):
        cliente, _ = self.crear_cliente("ADMIN")
        cursor = CursorUsuario(callproc_result={"sp_proximo_legajo_arg1": 1201})
        conexion = type("ConexionFalsa", (), {"commit": lambda self: None, "rollback": lambda self: None})()
        with patch.object(web, "_cursor", return_value=cursor), patch.object(web, "_db", return_value=conexion):
            respuesta = cliente.post(
                "/alumnos",
                data={
                    "csrf_token": "token-prueba",
                    "accion": "crear",
                    "dni": "99999999",
                    "apellido": "Prueba",
                    "nombre": "Alumno",
                    "fecha_nacimiento": "",
                    "email": "",
                },
                follow_redirects=False,
            )
        self.assertEqual(respuesta.status_code, 302)
        consulta_insert = next(i for i, sql in enumerate(cursor.consultas) if "INSERT INTO alumnos" in sql)
        self.assertEqual(cursor.parametros[consulta_insert][0], 1201)

    def test_encabezados_incorrectos_rechazan_el_archivo_antes_de_la_base(self):
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Datos"
        hoja.append(["nombre", "dni"])
        contenido = io.BytesIO()
        libro.save(contenido)
        contenido.seek(0)
        cliente, parche = self.crear_cliente("ADMIN")
        with tempfile.TemporaryDirectory() as temporal, patch.object(web, "CARPETA_LOGS", Path(temporal)), parche:
            respuesta = cliente.post(
                "/cargas",
                data={
                    "csrf_token": "token-prueba",
                    "plantilla": "Plantilla_Alumnos.xlsx",
                    "archivo": (contenido, "carga.xlsx"),
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            self.assertEqual(respuesta.status_code, 302)
            self.assertIn("/cargas/errores/", respuesta.location)
            self.assertEqual(len(list(Path(temporal).glob("errores_masivas_*.log"))), 1)

    def _archivo_alumnos(self, dni):
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Datos"
        hoja.append(["dni", "apellido", "nombre", "fecha_nacimiento", "email", "carrera", "anio_ingreso"])
        hoja.append([dni, "Pérez", "Ana", None, None, "Sistemas", 2026])
        contenido = io.BytesIO()
        libro.save(contenido)
        contenido.seek(0)
        return contenido

    def test_plantilla_de_alumnos_valida_inserta_filas_y_actualiza_lote(self):
        cliente, parche_cursor = self.crear_cliente("ADMIN")
        cursor = CursorUsuario()
        conexion = type("ConexionFalsa", (), {"commit": lambda self: None, "rollback": lambda self: None})()
        with patch.object(web, "_cursor", return_value=cursor), patch.object(web, "_db", return_value=conexion):
            respuesta = cliente.post(
                "/cargas",
                data={"csrf_token": "token-prueba", "plantilla": "Plantilla_Alumnos.xlsx", "archivo": (self._archivo_alumnos("42.123.456"), "alumnos.xlsx")},
                content_type="multipart/form-data",
                follow_redirects=False,
            )
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("INSERT INTO alumnos", "\n".join(cursor.consultas))
        self.assertIn("INSERT INTO matriculas", "\n".join(cursor.consultas))
        self.assertIn("UPDATE lotes_carga", "\n".join(cursor.consultas))

    def test_fila_invalida_se_rechaza_y_no_inserta_alumno(self):
        cliente, _ = self.crear_cliente("ADMIN")
        cursor = CursorUsuario()
        conexion = type("ConexionFalsa", (), {"commit": lambda self: None, "rollback": lambda self: None})()
        with tempfile.TemporaryDirectory() as temporal, patch.object(web, "CARPETA_LOGS", Path(temporal)), patch.object(web, "_cursor", return_value=cursor), patch.object(web, "_db", return_value=conexion):
            respuesta = cliente.post(
                "/cargas",
                data={"csrf_token": "token-prueba", "plantilla": "Plantilla_Alumnos.xlsx", "archivo": (self._archivo_alumnos("12A34"), "alumnos.xlsx")},
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            self.assertEqual(respuesta.status_code, 302)
            consultas = "\n".join(cursor.consultas)
            self.assertNotIn("INSERT INTO alumnos", consultas)
            log = next(Path(temporal).glob("errores_masivas_*.log")).read_text(encoding="utf-8")
            self.assertIn("dni", log)
            self.assertNotIn("12A34", log)


if __name__ == "__main__":
    unittest.main()
