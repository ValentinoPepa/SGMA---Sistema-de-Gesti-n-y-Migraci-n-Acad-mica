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
    def __init__(self, rol="ADMIN"):
        self.rol = rol
        self.ultima_consulta = ""
        self.consultas = []
        self.lastrowid = 1

    def execute(self, consulta, _parametros=None):
        self.ultima_consulta = consulta
        self.consultas.append(consulta)
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
        return (1200,)

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

    def test_directivo_no_puede_crear_alumnos(self):
        cliente, _ = self.crear_cliente("DIRECTIVO")
        with patch.object(web, "_cursor", return_value=CursorUsuario("DIRECTIVO")):
            respuesta = cliente.post("/alumnos", data={"accion": "crear"})
        self.assertEqual(respuesta.status_code, 403)

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
            self.assertIn("ERR_10_DNI_INVALID", log)
            self.assertNotIn("\tVALIDACION\t", log)
            self.assertNotIn("12A34", log)

    def test_descarga_plantilla_funciona_sin_carpeta_de_fases(self):
        from sgma.rutas import resolver_carpeta_plantillas

        with tempfile.TemporaryDirectory() as temporal, patch.dict(os.environ, {"SGMA_PLANTILLAS_DIR": ""}):
            ruta_aislada = Path(temporal) / "sgma" / "rutas.py"
            ruta_aislada.parent.mkdir(parents=True, exist_ok=True)
            ruta_aislada.touch()
            self.assertIsNone(resolver_carpeta_plantillas(ruta_aislada))

        cliente, parche = self.crear_cliente("ADMIN")
        with patch.object(web, "CARPETA_PLANTILLAS", None), parche:
            respuesta = cliente.get("/plantillas/Plantilla_Alumnos.xlsx")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("spreadsheetml", respuesta.content_type)

    def test_vista_previa_muestra_resumen_sin_insertar_y_confirmacion_inserta(self):
        cliente, _ = self.crear_cliente("ADMIN")
        cursor = CursorUsuario()
        conexion = type("ConexionFalsa", (), {"commit": lambda self: None, "rollback": lambda self: None})()
        with tempfile.TemporaryDirectory() as temporal, patch.object(web, "CARPETA_LOGS", Path(temporal)), patch.object(web, "_cursor", return_value=cursor), patch.object(web, "_db", return_value=conexion):
            prev = cliente.post(
                "/cargas",
                data={
                    "csrf_token": "token-prueba",
                    "accion": "previsualizar",
                    "plantilla": "Plantilla_Alumnos.xlsx",
                    "archivo": (self._archivo_alumnos("42.123.456"), "alumnos.xlsx"),
                },
                content_type="multipart/form-data",
            )
            self.assertEqual(prev.status_code, 200)
            self.assertIn(b"Vista previa antes de confirmar", prev.data)
            self.assertNotIn("INSERT INTO alumnos", "\n".join(cursor.consultas))

            with cliente.session_transaction() as sesion:
                token = sesion["carga_pendiente"]["token"]

            conf = cliente.post(
                "/cargas",
                data={"csrf_token": "token-prueba", "accion": "confirmar", "token_carga": token},
                follow_redirects=False,
            )
            self.assertEqual(conf.status_code, 302)
            self.assertIn("INSERT INTO alumnos", "\n".join(cursor.consultas))
            self.assertIn("UPDATE lotes_carga", "\n".join(cursor.consultas))

    def test_alumno_sin_carrera_carga_sin_matricula(self):
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Datos"
        hoja.append(["dni", "apellido", "nombre", "fecha_nacimiento", "email", "carrera", "anio_ingreso"])
        hoja.append(["42123456", "Pérez", "Ana", None, None, None, None])
        contenido = io.BytesIO()
        libro.save(contenido)
        contenido.seek(0)

        cliente, _ = self.crear_cliente("ADMIN")
        cursor = CursorUsuario()
        conexion = type("ConexionFalsa", (), {"commit": lambda self: None, "rollback": lambda self: None})()
        with patch.object(web, "_cursor", return_value=cursor), patch.object(web, "_db", return_value=conexion):
            respuesta = cliente.post(
                "/cargas",
                data={"csrf_token": "token-prueba", "plantilla": "Plantilla_Alumnos.xlsx", "archivo": (contenido, "alumnos.xlsx")},
                content_type="multipart/form-data",
                follow_redirects=False,
            )
        self.assertEqual(respuesta.status_code, 302)
        consultas = "\n".join(cursor.consultas)
        self.assertIn("INSERT INTO alumnos", consultas)
        self.assertNotIn("INSERT INTO matriculas", consultas)

    def test_carga_masiva_rechaza_archivo_que_supera_limite_de_filas(self):
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Datos"
        hoja.append(["dni", "apellido", "nombre", "fecha_nacimiento", "email", "carrera", "anio_ingreso"])
        for i in range(3):
            hoja.append([f"4212345{i}", "Pérez", "Ana", None, None, None, None])
        contenido = io.BytesIO()
        libro.save(contenido)
        contenido.seek(0)

        cliente, _ = self.crear_cliente("ADMIN")
        cursor = CursorUsuario()
        with patch.object(web, "MAX_FILAS_CARGA_MASIVA", 2), patch.object(web, "_cursor", return_value=cursor):
            respuesta = cliente.post(
                "/cargas",
                data={"csrf_token": "token-prueba", "plantilla": "Plantilla_Alumnos.xlsx", "archivo": (contenido, "alumnos.xlsx")},
                content_type="multipart/form-data",
                follow_redirects=False,
            )
        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn("INSERT INTO lotes_carga", "\n".join(cursor.consultas))

    def test_login_se_bloquea_tras_cinco_intentos_fallidos(self):
        from werkzeug.security import generate_password_hash

        app_prueba = web.create_app({"TESTING": True, "SECRET_KEY": "prueba-a6"})
        cliente = app_prueba.test_client()
        with cliente.session_transaction() as sesion:
            sesion["csrf"] = "token-prueba"

        class CursorLogin(CursorUsuario):
            def fetchone(self):
                if "password_hash" in self.ultima_consulta:
                    return {"id_usuario": 7, "password_hash": generate_password_hash("ClaveCorrecta123!")}
                return super().fetchone()

        with patch.object(web, "_cursor", return_value=CursorLogin()):
            for _ in range(4):
                resp = cliente.post(
                    "/login",
                    data={"csrf_token": "token-prueba", "username": "bedelia", "password": "mal"},
                )
                self.assertEqual(resp.status_code, 200)
            bloqueo = cliente.post(
                "/login",
                data={"csrf_token": "token-prueba", "username": "bedelia", "password": "mal"},
            )
            self.assertEqual(bloqueo.status_code, 429)
            aun_bloqueado = cliente.post(
                "/login",
                data={"csrf_token": "token-prueba", "username": "bedelia", "password": "ClaveCorrecta123!"},
            )
            self.assertEqual(aun_bloqueado.status_code, 429)

    def test_sesion_expira_tras_30_minutos_de_inactividad(self):
        import time

        cliente, parche = self.crear_cliente("ADMIN")
        with cliente.session_transaction() as sesion:
            sesion["ultima_actividad"] = time.time() - (31 * 60)
        with parche:
            respuesta = cliente.get("/usuarios", follow_redirects=False)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/login", respuesta.location)
        with cliente.session_transaction() as sesion:
            self.assertNotIn("usuario_id", sesion)

    def test_admin_solo_lee_datos_academicos(self):
        cliente, parche = self.crear_cliente("ADMIN")
        with parche:
            for ruta in ("/alumnos", "/carreras", "/materias", "/docentes", "/ciclos", "/cursadas", "/asistencias"):
                with self.subTest(get_ruta=ruta):
                    self.assertEqual(cliente.get(ruta).status_code, 200)
            for ruta in ("/alumnos", "/carreras", "/materias", "/docentes", "/ciclos", "/cursadas", "/asistencias"):
                with self.subTest(post_ruta=ruta):
                    resp = cliente.post(ruta, data={"csrf_token": "token-prueba"})
                    self.assertEqual(resp.status_code, 403)
            self.assertEqual(cliente.get("/alumnos/1/editar").status_code, 403)
            self.assertEqual(cliente.post("/alumnos/1/editar", data={"csrf_token": "token-prueba"}).status_code, 403)

    def test_preceptor_edita_estructura_docentes_y_alumnos(self):
        class CursorPreceptor(CursorUsuario):
            def fetchone(self):
                if "from alumnos where dni" in self.ultima_consulta.lower():
                    return None
                if "from docentes where dni" in self.ultima_consulta.lower():
                    return None
                return super().fetchone()

        cliente, _ = self.crear_cliente("PRECEPTOR")
        cursor = CursorPreceptor("PRECEPTOR")
        conexion = type("ConexionFalsa", (), {"commit": lambda self: None, "rollback": lambda self: None})()
        with patch.object(web, "_cursor", return_value=cursor), patch.object(web, "_db", return_value=conexion):
            r_carrera = cliente.post(
                "/carreras",
                data={"csrf_token": "token-prueba", "nombre": "Desarrollo de Software"},
                follow_redirects=False,
            )
            r_materia = cliente.post(
                "/materias",
                data={"csrf_token": "token-prueba", "id_carrera": "1", "codigo": "SIS101", "nombre": "Programación", "anio_nivel": "1"},
                follow_redirects=False,
            )
            r_docente = cliente.post(
                "/docentes",
                data={"csrf_token": "token-prueba", "dni": "30111222", "apellido": "Gómez", "nombre": "Laura", "email": "laura@example.edu"},
                follow_redirects=False,
            )
            r_alumno = cliente.post(
                "/alumnos",
                data={"csrf_token": "token-prueba", "accion": "crear", "dni": "40111222", "apellido": "Pérez", "nombre": "Ana"},
                follow_redirects=False,
            )
        self.assertEqual(r_carrera.status_code, 302)
        self.assertEqual(r_materia.status_code, 302)
        self.assertEqual(r_docente.status_code, 302)
        self.assertEqual(r_alumno.status_code, 302)
        consultas = "\n".join(cursor.consultas)
        self.assertIn("INSERT INTO carreras", consultas)
        self.assertIn("INSERT INTO materias", consultas)
        self.assertIn("INSERT INTO docentes", consultas)
        self.assertIn("INSERT INTO alumnos", consultas)

    def test_docente_ve_solo_legajo_apellido_y_nombre_de_sus_alumnos(self):
        class CursorDocente(CursorUsuario):
            def fetchone(self):
                q = self.ultima_consulta.lower()
                if "select id_docente from usuarios" in q:
                    return {"id_docente": 9}
                if "from inscripciones i join asignaciones_docentes" in q:
                    return {"1": 1}
                return super().fetchone()

            def fetchall(self):
                q = self.ultima_consulta.lower()
                if "from alumnos" in q:
                    return [{"id_alumno": 10, "legajo": 1001, "apellido": "Pérez", "nombre": "Ana"}]
                return []

        cliente, _ = self.crear_cliente("DOCENTE")
        cursor = CursorDocente("DOCENTE")
        with patch.object(web, "_cursor", return_value=cursor):
            resp_alumnos = cliente.get("/alumnos")
            resp_busqueda = cliente.get("/busqueda?q=1001")
            resp_docentes = cliente.get("/docentes")

        self.assertEqual(resp_alumnos.status_code, 200)
        html_alumnos = resp_alumnos.data.decode("utf-8")
        self.assertIn("1001", html_alumnos)
        self.assertIn("Pérez, Ana", html_alumnos)
        self.assertNotIn("<th>DNI</th>", html_alumnos)
        self.assertNotIn("<th>E-mail</th>", html_alumnos)

        self.assertEqual(resp_busqueda.status_code, 200)
        html_busqueda = resp_busqueda.data.decode("utf-8")
        self.assertIn("1001", html_busqueda)
        self.assertIn("Pérez, Ana", html_busqueda)
        self.assertNotIn("DNI:", html_busqueda)
        self.assertNotIn("Matrículas", html_busqueda)

        self.assertEqual(resp_docentes.status_code, 403)


if __name__ == "__main__":
    unittest.main()
