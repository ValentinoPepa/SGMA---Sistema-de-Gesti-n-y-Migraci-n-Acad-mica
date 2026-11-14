"""Panel web inicial del SGMA: autenticación, usuarios y control por roles."""

from __future__ import annotations

import hmac
import io
import os
import re
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from pathlib import Path
from typing import Any, Callable

import mysql.connector
from openpyxl import load_workbook
from flask import Flask, abort, flash, g, redirect, render_template, request, send_file, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .validaciones import normalizar_dni, normalizar_email, normalizar_fecha, normalizar_nombre, normalizar_nota
from .errores import RegistroErrores
from .rutas import buscar_carpeta_v11


ROLES = ("ADMIN", "PRECEPTOR", "DOCENTE", "DIRECTIVO")
CARPETA_V11 = buscar_carpeta_v11()
CARPETA_PLANTILLAS = CARPETA_V11 / "Fase 2 Diseño y Base de Datos"
CARPETA_LOGS = Path(__file__).resolve().parents[1] / "logs"
PLANTILLAS_CARGA = {
    "Plantilla_Alumnos.xlsx": ("alumnos", ("dni", "apellido", "nombre", "fecha_nacimiento", "email", "carrera", "anio_ingreso")),
    "Plantilla_Inscripciones.xlsx": ("inscripciones", ("dni_alumno", "codigo_materia", "anio_ciclo", "condicion_cursada")),
    "Plantilla_Actas.xlsx": ("actas_examen", ("dni_alumno", "codigo_materia", "fecha_examen", "libro", "folio", "nota", "condicion")),
}


def _conexion():
    requeridas = ("SGMA_DB_HOST", "SGMA_DB_USER", "SGMA_DB_PASSWORD")
    faltantes = [nombre for nombre in requeridas if not os.getenv(nombre)]
    if faltantes:
        raise RuntimeError("Faltan variables de entorno: " + ", ".join(faltantes))
    return mysql.connector.connect(
        host=os.environ["SGMA_DB_HOST"],
        port=int(os.getenv("SGMA_DB_PORT", "3306")),
        user=os.environ["SGMA_DB_USER"],
        password=os.environ["SGMA_DB_PASSWORD"],
        database=os.getenv("SGMA_DB_NAME", "gestion_academica"),
        autocommit=False,
    )


def _db():
    if "conexion" not in g:
        g.conexion = _conexion()
        cursor = g.conexion.cursor()
        try:
            cursor.execute("SET @app_user_id = %s", (session.get("usuario_id"),))
        finally:
            cursor.close()
    return g.conexion


def _cursor():
    return _db().cursor(dictionary=True, buffered=True)


def _token_csrf() -> str:
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def _validar_csrf() -> None:
    recibido = request.form.get("csrf_token", "")
    esperado = session.get("csrf", "")
    if not esperado or not hmac.compare_digest(recibido, esperado):
        abort(400, description="La sesión del formulario venció. Vuelva a cargar la página.")


def requiere_login(vista: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(vista)
    def envoltura(*args: Any, **kwargs: Any):
        if not getattr(g, "usuario", None):
            return redirect(url_for("login", next=request.path))
        return vista(*args, **kwargs)
    return envoltura


def requiere_roles(*roles: str):
    def decorador(vista: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(vista)
        @requiere_login
        def envoltura(*args: Any, **kwargs: Any):
            if g.usuario["rol"] not in roles:
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates")
    clave = os.getenv("SGMA_SECRET_KEY")
    if not clave and not test_config:
        raise RuntimeError("Defina SGMA_SECRET_KEY con una clave aleatoria antes de iniciar el panel.")
    app.config.update(
        SECRET_KEY=clave or "solo-configuracion-local",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SGMA_COOKIE_SECURE", "false").lower() == "true",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    @app.before_request
    def cargar_usuario():
        g.usuario = None
        usuario_id = session.get("usuario_id")
        if usuario_id is None:
            return
        cursor = _cursor()
        try:
            cursor.execute(
                "SELECT u.id_usuario, u.username, u.id_rol, r.nombre AS rol "
                "FROM usuarios u JOIN roles r ON r.id_rol = u.id_rol "
                "WHERE u.id_usuario = %s AND u.activo = TRUE",
                (usuario_id,),
            )
            g.usuario = cursor.fetchone()
        finally:
            cursor.close()
        if g.usuario is None:
            session.clear()

    @app.teardown_appcontext
    def cerrar_conexion(_error: BaseException | None) -> None:
        conexion = g.pop("conexion", None)
        if conexion is not None:
            conexion.close()

    @app.context_processor
    def datos_comunes():
        return {"csrf_token": _token_csrf, "usuario_actual": getattr(g, "usuario", None)}

    @app.get("/")
    @requiere_login
    def inicio():
        return render_template("inicio.html")

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        cursor = _cursor()
        try:
            cursor.execute("SELECT COUNT(*) AS cantidad FROM usuarios")
            if cursor.fetchone()["cantidad"]:
                return redirect(url_for("login"))
            if request.method == "POST":
                _validar_csrf()
                username = request.form.get("username", "").strip()
                password = request.form.get("password", "")
                confirmar = request.form.get("confirmar", "")
                if len(username) < 3 or len(username) > 50:
                    flash("El usuario debe tener entre 3 y 50 caracteres.", "error")
                elif len(password) < 12:
                    flash("La contraseña debe tener al menos 12 caracteres.", "error")
                elif password != confirmar:
                    flash("Las contraseñas no coinciden.", "error")
                else:
                    cursor.execute("SELECT id_rol FROM roles WHERE nombre = 'ADMIN'")
                    rol = cursor.fetchone()
                    if rol is None:
                        abort(500, description="Falta el rol ADMIN. Ejecute primero gestion_academica.sql.")
                    cursor.execute(
                        "INSERT INTO usuarios (username, password_hash, id_rol) VALUES (%s, %s, %s)",
                        (username, generate_password_hash(password), rol["id_rol"]),
                    )
                    _db().commit()
                    flash("Administrador inicial creado. Ya puede iniciar sesión.", "success")
                    return redirect(url_for("login"))
        finally:
            cursor.close()
        return render_template("setup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            _validar_csrf()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            cursor = _cursor()
            try:
                cursor.execute(
                    "SELECT u.id_usuario, u.password_hash FROM usuarios u "
                    "WHERE u.username = %s AND u.activo = TRUE",
                    (username,),
                )
                cuenta = cursor.fetchone()
            finally:
                cursor.close()
            if cuenta and check_password_hash(cuenta["password_hash"], password):
                destino = request.args.get("next", "")
                # Se permiten únicamente rutas del mismo sitio para evitar redirecciones externas.
                if not destino.startswith("/") or destino.startswith("//"):
                    destino = url_for("inicio")
                session.clear()
                session["usuario_id"] = cuenta["id_usuario"]
                session.permanent = True
                _token_csrf()
                return redirect(destino)
            flash("Usuario o contraseña incorrectos.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @requiere_login
    def logout():
        _validar_csrf()
        session.clear()
        return redirect(url_for("login"))

    @app.route("/usuarios", methods=["GET", "POST"])
    @requiere_roles("ADMIN")
    def usuarios():
        cursor = _cursor()
        try:
            if request.method == "POST":
                _validar_csrf()
                accion = request.form.get("accion")
                if accion == "crear":
                    username = request.form.get("username", "").strip()
                    password = request.form.get("password", "")
                    rol_nombre = request.form.get("rol", "")
                    id_docente_texto = request.form.get("id_docente", "").strip()
                    id_docente = int(id_docente_texto) if id_docente_texto.isdigit() else None
                    if len(username) < 3 or len(username) > 50 or len(password) < 12 or rol_nombre not in ROLES:
                        flash("Revise usuario, contraseña (mínimo 12 caracteres) y rol.", "error")
                    else:
                        cursor.execute("SELECT id_rol FROM roles WHERE nombre = %s", (rol_nombre,))
                        rol = cursor.fetchone()
                        if rol is None:
                            flash("El rol indicado no existe en la base de datos.", "error")
                        elif rol_nombre == "DOCENTE" and id_docente is None:
                            flash("Los usuarios con rol DOCENTE deben vincularse con un docente.", "error")
                        else:
                            cursor.execute(
                                "INSERT INTO usuarios (username, password_hash, id_rol, id_docente) VALUES (%s, %s, %s, %s)",
                                (username, generate_password_hash(password), rol["id_rol"], id_docente),
                            )
                            _db().commit()
                            flash("Usuario creado.", "success")
                            return redirect(url_for("usuarios"))
                elif accion == "desactivar":
                    usuario_id = request.form.get("usuario_id", "")
                    if usuario_id.isdigit() and int(usuario_id) != g.usuario["id_usuario"]:
                        cursor.execute("UPDATE usuarios SET activo = FALSE WHERE id_usuario = %s", (int(usuario_id),))
                        _db().commit()
                        flash("Usuario desactivado.", "success")
                        return redirect(url_for("usuarios"))
                    flash("No puede desactivar su propia cuenta.", "error")

            cursor.execute(
                "SELECT u.id_usuario, u.username, u.activo, r.nombre AS rol, "
                "d.nombre AS docente_nombre, d.apellido AS docente_apellido "
                "FROM usuarios u JOIN roles r ON r.id_rol = u.id_rol "
                "LEFT JOIN docentes d ON d.id_docente = u.id_docente ORDER BY u.username"
            )
            cuentas = cursor.fetchall()
            cursor.execute("SELECT id_docente, nombre, apellido FROM docentes WHERE activo = TRUE ORDER BY apellido, nombre")
            docentes = cursor.fetchall()
        finally:
            cursor.close()
        return render_template("usuarios.html", cuentas=cuentas, docentes=docentes, roles=ROLES)

    @app.route("/alumnos", methods=["GET", "POST"])
    @requiere_roles("ADMIN", "PRECEPTOR", "DIRECTIVO", "DOCENTE")
    def alumnos():
        cursor = _cursor()
        puede_editar = g.usuario["rol"] in {"ADMIN", "PRECEPTOR"}
        try:
            if request.method == "POST":
                if not puede_editar:
                    abort(403)
                _validar_csrf()
                accion = request.form.get("accion")
                if accion == "crear":
                    dni = normalizar_dni(request.form.get("dni"))
                    apellido = normalizar_nombre(request.form.get("apellido"), "apellido")
                    nombre = normalizar_nombre(request.form.get("nombre"), "nombre")
                    email = normalizar_email(request.form.get("email"))
                    fecha_texto = request.form.get("fecha_nacimiento", "").strip()
                    fecha = normalizar_fecha(fecha_texto, campo="fecha_nacimiento", no_futura=True) if fecha_texto else None
                    errores = [*dni.errores, *apellido.errores, *nombre.errores, *email.errores]
                    if fecha and not fecha.valido:
                        errores.extend(fecha.errores)
                    if errores:
                        for error in errores:
                            flash(error.mensaje, "error")
                    else:
                        cursor.execute("SELECT id_alumno FROM alumnos WHERE dni = %s LIMIT 1", (dni.valor,))
                        if cursor.fetchone():
                            flash("El DNI ya está registrado en alumnos.", "error")
                        else:
                            # El procedimiento bloquea el contador durante la transacción,
                            # así dos altas simultáneas no reciben el mismo legajo.
                            parametros = cursor.callproc("sp_proximo_legajo", [0])
                            legajo = parametros[0]
                            cursor.execute(
                                "INSERT INTO alumnos (legajo, dni, apellido, nombre, fecha_nacimiento, email, origen) "
                                "VALUES (%s, %s, %s, %s, %s, %s, 'MANUAL')",
                                (legajo, dni.valor, apellido.valor, nombre.valor, fecha.valor if fecha else None, email.valor),
                            )
                            _db().commit()
                            flash(f"Alumno creado con legajo {legajo}.", "success")
                            return redirect(url_for("alumnos"))
                elif accion == "desactivar":
                    id_alumno = request.form.get("id_alumno", "")
                    if id_alumno.isdigit():
                        cursor.execute("UPDATE alumnos SET activo = FALSE WHERE id_alumno = %s", (int(id_alumno),))
                        _db().commit()
                        flash("Alumno dado de baja lógica.", "success")
                        return redirect(url_for("alumnos"))

            consulta = request.args.get("q", "").strip()
            if consulta:
                patron = f"%{consulta}%"
                cursor.execute(
                    "SELECT id_alumno, legajo, dni, apellido, nombre, email, activo FROM alumnos "
                    "WHERE dni LIKE %s OR CAST(legajo AS CHAR) LIKE %s ORDER BY apellido, nombre LIMIT 100",
                    (patron, patron),
                )
            else:
                cursor.execute(
                    "SELECT id_alumno, legajo, dni, apellido, nombre, email, activo FROM alumnos "
                    "ORDER BY apellido, nombre LIMIT 100"
                )
            registros = cursor.fetchall()
        finally:
            cursor.close()
        return render_template("alumnos.html", alumnos=registros, puede_editar=puede_editar, busqueda=request.args.get("q", ""))

    @app.route("/carreras", methods=["GET", "POST"])
    @requiere_roles("ADMIN", "PRECEPTOR", "DIRECTIVO", "DOCENTE")
    def carreras():
        cursor = _cursor()
        puede_editar = g.usuario["rol"] == "ADMIN"
        try:
            if request.method == "POST":
                if not puede_editar:
                    abort(403)
                _validar_csrf()
                nombre = request.form.get("nombre", "").strip()
                if not nombre or len(nombre) > 100:
                    flash("El nombre de la carrera es obligatorio y no puede superar 100 caracteres.", "error")
                else:
                    try:
                        cursor.execute("INSERT INTO carreras (nombre) VALUES (%s)", (nombre,))
                        _db().commit()
                        flash("Carrera creada.", "success")
                        return redirect(url_for("carreras"))
                    except mysql.connector.IntegrityError:
                        _db().rollback()
                        flash("Ya existe una carrera con ese nombre.", "error")
            cursor.execute("SELECT id_carrera, nombre, activa FROM carreras ORDER BY nombre")
            registros = cursor.fetchall()
        finally:
            cursor.close()
        return render_template("carreras.html", carreras=registros, puede_editar=puede_editar)

    @app.route("/materias", methods=["GET", "POST"])
    @requiere_roles("ADMIN", "PRECEPTOR", "DIRECTIVO", "DOCENTE")
    def materias():
        cursor = _cursor()
        puede_editar = g.usuario["rol"] == "ADMIN"
        try:
            if request.method == "POST":
                if not puede_editar:
                    abort(403)
                _validar_csrf()
                carrera_id = request.form.get("id_carrera", "")
                codigo = request.form.get("codigo", "").strip().replace("-", "").replace(" ", "").upper()
                nombre = request.form.get("nombre", "").strip()
                try:
                    anio = int(request.form.get("anio_nivel", ""))
                except ValueError:
                    anio = 0
                if not carrera_id.isdigit() or not codigo or len(codigo) > 10 or not nombre or len(nombre) > 100 or anio not in range(1, 6):
                    flash("Revise carrera, código, nombre y año (1 a 5).", "error")
                else:
                    try:
                        cursor.execute(
                            "INSERT INTO materias (id_carrera, codigo, nombre, anio_nivel) VALUES (%s, %s, %s, %s)",
                            (int(carrera_id), codigo, nombre, anio),
                        )
                        _db().commit()
                        flash("Materia creada.", "success")
                        return redirect(url_for("materias"))
                    except mysql.connector.IntegrityError:
                        _db().rollback()
                        flash("La carrera no existe o el código de materia ya está utilizado.", "error")
            cursor.execute("SELECT id_carrera, nombre FROM carreras WHERE activa = TRUE ORDER BY nombre")
            opciones_carrera = cursor.fetchall()
            cursor.execute(
                "SELECT m.id_materia, m.codigo, m.nombre, m.anio_nivel, m.activa, c.nombre AS carrera "
                "FROM materias m JOIN carreras c ON c.id_carrera = m.id_carrera ORDER BY c.nombre, m.anio_nivel, m.nombre"
            )
            registros = cursor.fetchall()
        finally:
            cursor.close()
        return render_template("materias.html", materias=registros, carreras=opciones_carrera, puede_editar=puede_editar)

    @app.route("/docentes", methods=["GET", "POST"])
    @requiere_roles("ADMIN", "PRECEPTOR", "DIRECTIVO")
    def docentes():
        cursor = _cursor()
        puede_editar = g.usuario["rol"] == "ADMIN"
        try:
            if request.method == "POST":
                if not puede_editar:
                    abort(403)
                _validar_csrf()
                dni = normalizar_dni(request.form.get("dni"))
                apellido = normalizar_nombre(request.form.get("apellido"), "apellido")
                nombre = normalizar_nombre(request.form.get("nombre"), "nombre")
                email = normalizar_email(request.form.get("email"))
                errores = [*dni.errores, *apellido.errores, *nombre.errores, *email.errores]
                if errores:
                    for error in errores:
                        flash(error.mensaje, "error")
                else:
                    cursor.execute("SELECT id_docente FROM docentes WHERE dni = %s LIMIT 1", (dni.valor,))
                    if cursor.fetchone():
                        flash("El DNI ya está registrado en docentes.", "error")
                    else:
                        cursor.execute(
                            "INSERT INTO docentes (dni, apellido, nombre, email) VALUES (%s, %s, %s, %s)",
                            (dni.valor, apellido.valor, nombre.valor, email.valor),
                        )
                        _db().commit()
                        flash("Docente creado.", "success")
                        return redirect(url_for("docentes"))
            cursor.execute("SELECT id_docente, dni, apellido, nombre, email, activo FROM docentes ORDER BY apellido, nombre")
            registros = cursor.fetchall()
        finally:
            cursor.close()
        return render_template("docentes.html", docentes=registros, puede_editar=puede_editar)

    @app.route("/ciclos", methods=["GET", "POST"])
    @requiere_roles("ADMIN", "PRECEPTOR", "DIRECTIVO", "DOCENTE")
    def ciclos():
        cursor = _cursor()
        puede_editar = g.usuario["rol"] in {"ADMIN", "PRECEPTOR"}
        try:
            if request.method == "POST":
                if not puede_editar:
                    abort(403)
                _validar_csrf()
                try:
                    anio = int(request.form.get("anio", ""))
                    inicio = normalizar_fecha(request.form.get("fecha_inicio"), campo="fecha_inicio")
                    fin = normalizar_fecha(request.form.get("fecha_fin"), campo="fecha_fin")
                    if not 2000 <= anio <= 2200 or not inicio.valido or not fin.valido or fin.valor <= inicio.valor:
                        raise ValueError
                    cursor.execute(
                        "INSERT INTO ciclos_lectivos (anio, fecha_inicio, fecha_fin) VALUES (%s, %s, %s)",
                        (anio, inicio.valor, fin.valor),
                    )
                    _db().commit()
                    flash("Ciclo lectivo creado.", "success")
                    return redirect(url_for("ciclos"))
                except (ValueError, TypeError):
                    flash("Revise el año y el rango de fechas del ciclo lectivo.", "error")
                except mysql.connector.IntegrityError:
                    _db().rollback()
                    flash("Ya existe un ciclo para ese año.", "error")
            cursor.execute("SELECT id_ciclo, anio, fecha_inicio, fecha_fin FROM ciclos_lectivos ORDER BY anio DESC")
            registros = cursor.fetchall()
        finally:
            cursor.close()
        return render_template("ciclos.html", ciclos=registros, puede_editar=puede_editar)

    @app.route("/cursadas", methods=["GET", "POST"])
    @requiere_roles("ADMIN", "PRECEPTOR", "DOCENTE", "DIRECTIVO")
    def cursadas():
        cursor = _cursor()
        rol = g.usuario["rol"]
        puede_administrar = rol in {"ADMIN", "PRECEPTOR"}

        def docente_autorizado(materia_id: int, ciclo_id: int) -> bool:
            cursor.execute("SELECT id_docente FROM usuarios WHERE id_usuario = %s", (g.usuario["id_usuario"],))
            cuenta = cursor.fetchone()
            if not cuenta or not cuenta["id_docente"]:
                return False
            cursor.execute(
                "SELECT 1 FROM asignaciones_docentes WHERE id_docente = %s AND id_materia = %s AND id_ciclo = %s LIMIT 1",
                (cuenta["id_docente"], materia_id, ciclo_id),
            )
            return cursor.fetchone() is not None

        try:
            if request.method == "POST":
                _validar_csrf()
                accion = request.form.get("accion")
                if accion == "inscribir_cursada":
                    if not puede_administrar:
                        abort(403)
                    dni = normalizar_dni(request.form.get("dni"))
                    codigo = request.form.get("codigo_materia", "").strip().replace("-", "").replace(" ", "").upper()
                    ciclo_anio = request.form.get("anio_ciclo", "")
                    condicion = request.form.get("condicion_cursada", "CURSANDO")
                    if not dni.valido or condicion not in {"CURSANDO", "REGULAR", "PROMOCIONADO", "LIBRE"}:
                        flash("DNI o condición de cursada inválidos.", "error")
                    else:
                        cursor.execute("SELECT id_alumno FROM alumnos WHERE dni = %s AND activo = TRUE", (dni.valor,))
                        alumno = cursor.fetchone()
                        cursor.execute("SELECT id_materia FROM materias WHERE codigo = %s AND activa = TRUE", (codigo,))
                        materia = cursor.fetchone()
                        cursor.execute("SELECT id_ciclo FROM ciclos_lectivos WHERE anio = %s", (ciclo_anio,))
                        ciclo = cursor.fetchone()
                        if not alumno or not materia or not ciclo:
                            flash("No se encontró el alumno, la materia o el ciclo lectivo.", "error")
                        else:
                            cursor.execute(
                                "SELECT m.id_materia_requerida FROM correlatividades m "
                                "WHERE m.id_materia = %s AND NOT EXISTS ("
                                "SELECT 1 FROM actas_examen a WHERE a.id_alumno = %s AND a.id_materia = m.id_materia_requerida "
                                "AND a.estado = 'APROBADO' AND a.activo = TRUE)",
                                (materia["id_materia"], alumno["id_alumno"]),
                            )
                            faltantes = cursor.fetchall()
                            if faltantes:
                                flash("No se puede inscribir: faltan correlativas aprobadas.", "error")
                            else:
                                try:
                                    cursor.execute(
                                        "INSERT INTO inscripciones (id_alumno, id_materia, id_ciclo, condicion_cursada) VALUES (%s, %s, %s, %s)",
                                        (alumno["id_alumno"], materia["id_materia"], ciclo["id_ciclo"], condicion),
                                    )
                                    _db().commit()
                                    flash("Inscripción a cursada creada.", "success")
                                    return redirect(url_for("cursadas"))
                                except mysql.connector.IntegrityError:
                                    _db().rollback()
                                    flash("La inscripción ya existe o alguna referencia dejó de estar disponible.", "error")
                elif accion == "crear_mesa":
                    if not puede_administrar:
                        abort(403)
                    try:
                        materia_id = int(request.form.get("id_materia", ""))
                        ciclo_id = int(request.form.get("id_ciclo", ""))
                        llamado = int(request.form.get("llamado", "1"))
                        fecha = normalizar_fecha(request.form.get("fecha"), campo="fecha", no_futura=False)
                        if llamado < 1 or not fecha.valido:
                            raise ValueError
                        cursor.execute(
                            "INSERT INTO mesas_examen (id_materia, id_ciclo, fecha, llamado) VALUES (%s, %s, %s, %s)",
                            (materia_id, ciclo_id, fecha.valor, llamado),
                        )
                        _db().commit()
                        flash("Mesa de examen creada.", "success")
                        return redirect(url_for("cursadas"))
                    except (ValueError, TypeError):
                        flash("Revise materia, ciclo, fecha y llamado.", "error")
                    except mysql.connector.IntegrityError:
                        _db().rollback()
                        flash("La mesa ya existe o la materia/ciclo no es válido.", "error")
                elif accion == "inscribir_examen":
                    if not puede_administrar:
                        abort(403)
                    dni = normalizar_dni(request.form.get("dni"))
                    mesa_id = request.form.get("id_mesa", "")
                    if not dni.valido or not mesa_id.isdigit():
                        flash("DNI o mesa inválidos.", "error")
                    else:
                        cursor.execute("SELECT id_alumno FROM alumnos WHERE dni = %s AND activo = TRUE", (dni.valor,))
                        alumno = cursor.fetchone()
                        cursor.execute("SELECT id_mesa, id_materia FROM mesas_examen WHERE id_mesa = %s AND activo = TRUE", (int(mesa_id),))
                        mesa = cursor.fetchone()
                        if not alumno or not mesa:
                            flash("No se encontró el alumno o la mesa de examen.", "error")
                        else:
                            cursor.execute(
                                "SELECT cr.id_materia_requerida FROM correlatividades cr "
                                "WHERE cr.id_materia = %s AND NOT EXISTS (SELECT 1 FROM actas_examen ae "
                                "WHERE ae.id_alumno = %s AND ae.id_materia = cr.id_materia_requerida "
                                "AND ae.estado = 'APROBADO' AND ae.activo = TRUE)",
                                (mesa["id_materia"], alumno["id_alumno"]),
                            )
                            if cursor.fetchone():
                                flash("No se puede inscribir: faltan correlativas aprobadas.", "error")
                            else:
                                try:
                                    cursor.execute("INSERT INTO inscripciones_examen (id_alumno, id_mesa) VALUES (%s, %s)", (alumno["id_alumno"], mesa["id_mesa"]))
                                    _db().commit()
                                    flash("Inscripción a examen creada.", "success")
                                    return redirect(url_for("cursadas"))
                                except mysql.connector.IntegrityError:
                                    _db().rollback()
                                    flash("El alumno ya está inscripto en esa mesa.", "error")
                elif accion in {"registrar_nota", "registrar_acta"}:
                    if rol not in {"ADMIN", "PRECEPTOR", "DOCENTE"}:
                        abort(403)
                    try:
                        if accion == "registrar_nota":
                            inscripcion_id = int(request.form.get("id_inscripcion", ""))
                            instancia = request.form.get("instancia", "").strip()
                            if not instancia or len(instancia) > 30:
                                raise ValueError("La instancia de evaluación es obligatoria y no puede superar 30 caracteres.")
                            cursor.execute("SELECT id_materia, id_ciclo FROM inscripciones WHERE id_inscripcion = %s AND activo = TRUE", (inscripcion_id,))
                            inscripcion = cursor.fetchone()
                            if not inscripcion:
                                raise ValueError("No existe la inscripción activa.")
                            materia_id, ciclo_id = inscripcion["id_materia"], inscripcion["id_ciclo"]
                            nota = normalizar_nota(request.form.get("nota"))
                            fecha = normalizar_fecha(request.form.get("fecha"), campo="fecha")
                            if not nota.valido or not fecha.valido:
                                raise ValueError((nota.errores or fecha.errores)[0].mensaje)
                            if rol == "DOCENTE" and not docente_autorizado(materia_id, ciclo_id):
                                abort(403)
                            cursor.execute(
                                "INSERT INTO notas_cursada (id_inscripcion, instancia, nota, fecha) VALUES (%s, %s, %s, %s)",
                                (inscripcion_id, instancia, nota.valor, fecha.valor),
                            )
                        else:
                            dni = normalizar_dni(request.form.get("dni"))
                            materia_id = int(request.form.get("id_materia", ""))
                            ciclo_id = int(request.form.get("id_ciclo", ""))
                            fecha = normalizar_fecha(request.form.get("fecha_examen"), campo="fecha_examen", no_futura=True)
                            estado = request.form.get("estado", "")
                            libro, folio = request.form.get("libro", "").strip(), request.form.get("folio", "").strip()
                            if not dni.valido or not fecha.valido or estado not in {"APROBADO", "DESAPROBADO", "AUSENTE"} or not libro or not folio:
                                raise ValueError("Revise DNI, fecha, estado, libro y folio.")
                            if rol == "DOCENTE" and not docente_autorizado(materia_id, ciclo_id):
                                abort(403)
                            cursor.execute("SELECT id_alumno FROM alumnos WHERE dni = %s AND activo = TRUE", (dni.valor,))
                            alumno = cursor.fetchone()
                            nota_texto = request.form.get("nota", "").strip()
                            if estado == "AUSENTE":
                                nota_valor = None
                            else:
                                nota_resultado = normalizar_nota(nota_texto)
                                if not nota_resultado.valido:
                                    raise ValueError(nota_resultado.errores[0].mensaje)
                                nota_valor = nota_resultado.valor
                            if not alumno:
                                raise ValueError("No existe un alumno activo con ese DNI.")
                            mesa_id = request.form.get("id_mesa", "").strip()
                            mesa_id = int(mesa_id) if mesa_id.isdigit() else None
                            if rol == "DOCENTE" and mesa_id is None:
                                raise ValueError("El docente debe asociar el acta a una mesa de su materia asignada.")
                            cursor.execute(
                                "INSERT INTO actas_examen (id_alumno, id_materia, id_mesa, fecha_examen, libro, folio, nota, estado, origen) "
                                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'MANUAL')",
                                (alumno["id_alumno"], materia_id, mesa_id, fecha.valor, libro, folio, nota_valor, estado),
                            )
                        _db().commit()
                        flash("Registro académico guardado.", "success")
                        return redirect(url_for("cursadas"))
                    except ValueError as error:
                        flash(str(error), "error")
                    except mysql.connector.IntegrityError:
                        _db().rollback()
                        flash("No se pudo guardar: revise que el registro no esté duplicado y que sus referencias existan.", "error")

            cursor.execute("SELECT id_materia, codigo, nombre FROM materias WHERE activa = TRUE ORDER BY codigo")
            materias_opciones = cursor.fetchall()
            cursor.execute("SELECT id_ciclo, anio FROM ciclos_lectivos ORDER BY anio DESC")
            ciclos_opciones = cursor.fetchall()
            cursor.execute("SELECT id_mesa, fecha, llamado, id_materia, id_ciclo FROM mesas_examen WHERE activo = TRUE ORDER BY fecha DESC")
            mesas_opciones = cursor.fetchall()
            if rol == "DOCENTE":
                cursor.execute("SELECT id_docente FROM usuarios WHERE id_usuario = %s", (g.usuario["id_usuario"],))
                perfil_docente = cursor.fetchone()
                if perfil_docente and perfil_docente["id_docente"]:
                    cursor.execute(
                        "SELECT id_materia, id_ciclo FROM asignaciones_docentes WHERE id_docente = %s",
                        (perfil_docente["id_docente"],),
                    )
                    asignaciones = cursor.fetchall()
                    claves_asignadas = {(r["id_materia"], r["id_ciclo"]) for r in asignaciones}
                    materias_asignadas = {r["id_materia"] for r in asignaciones}
                    ciclos_asignados = {r["id_ciclo"] for r in asignaciones}
                    materias_opciones = [m for m in materias_opciones if m["id_materia"] in materias_asignadas]
                    ciclos_opciones = [c for c in ciclos_opciones if c["id_ciclo"] in ciclos_asignados]
                    mesas_opciones = [m for m in mesas_opciones if (m["id_materia"], m["id_ciclo"]) in claves_asignadas]
            consulta_inscripciones = (
                "SELECT i.id_inscripcion, a.legajo, a.apellido, a.nombre, m.codigo, c.anio, i.condicion_cursada "
                "FROM inscripciones i JOIN alumnos a ON a.id_alumno=i.id_alumno "
                "JOIN materias m ON m.id_materia=i.id_materia JOIN ciclos_lectivos c ON c.id_ciclo=i.id_ciclo "
                "WHERE i.activo=TRUE"
            )
            if rol == "DOCENTE":
                consulta_inscripciones += (
                    " AND EXISTS (SELECT 1 FROM usuarios u JOIN asignaciones_docentes ad ON ad.id_docente=u.id_docente "
                    "WHERE u.id_usuario=%s AND ad.id_materia=i.id_materia AND ad.id_ciclo=i.id_ciclo)"
                )
                cursor.execute(consulta_inscripciones + " ORDER BY c.anio DESC, a.apellido, a.nombre LIMIT 200", (g.usuario["id_usuario"],))
            else:
                cursor.execute(consulta_inscripciones + " ORDER BY c.anio DESC, a.apellido, a.nombre LIMIT 200")
            inscripciones = cursor.fetchall()
            consulta_notas = (
                "SELECT n.id_nota, n.id_inscripcion, n.instancia, n.nota, n.fecha FROM notas_cursada n "
                "JOIN inscripciones i ON i.id_inscripcion=n.id_inscripcion WHERE n.activo=TRUE"
            )
            if rol == "DOCENTE":
                consulta_notas += (
                    " AND EXISTS (SELECT 1 FROM usuarios u JOIN asignaciones_docentes ad ON ad.id_docente=u.id_docente "
                    "WHERE u.id_usuario=%s AND ad.id_materia=i.id_materia AND ad.id_ciclo=i.id_ciclo)"
                )
                cursor.execute(consulta_notas + " ORDER BY n.fecha DESC LIMIT 100", (g.usuario["id_usuario"],))
            else:
                cursor.execute(consulta_notas + " ORDER BY n.fecha DESC LIMIT 100")
            notas = cursor.fetchall()
            consulta_actas = (
                "SELECT ae.id_acta, a.legajo, a.apellido, a.nombre, m.codigo, ae.fecha_examen, ae.libro, ae.folio, ae.nota, ae.estado "
                "FROM actas_examen ae JOIN alumnos a ON a.id_alumno=ae.id_alumno JOIN materias m ON m.id_materia=ae.id_materia "
                "WHERE ae.activo=TRUE"
            )
            if rol == "DOCENTE":
                consulta_actas += (
                    " AND ae.id_mesa IS NOT NULL AND EXISTS (SELECT 1 FROM usuarios u "
                    "JOIN asignaciones_docentes ad ON ad.id_docente=u.id_docente "
                    "JOIN mesas_examen mx ON mx.id_materia=ad.id_materia AND mx.id_ciclo=ad.id_ciclo "
                    "WHERE u.id_usuario=%s AND mx.id_mesa=ae.id_mesa)"
                )
                cursor.execute(consulta_actas + " ORDER BY ae.fecha_examen DESC LIMIT 100", (g.usuario["id_usuario"],))
            else:
                cursor.execute(consulta_actas + " ORDER BY ae.fecha_examen DESC LIMIT 100")
            actas = cursor.fetchall()
        finally:
            cursor.close()
        return render_template(
            "cursadas.html", materias=materias_opciones, ciclos=ciclos_opciones, mesas=mesas_opciones,
            inscripciones=inscripciones, notas=notas, actas=actas, puede_administrar=puede_administrar,
            puede_cargar=rol in {"ADMIN", "PRECEPTOR", "DOCENTE"}, rol=rol,
        )

    @app.route("/asistencias", methods=["GET", "POST"])
    @requiere_roles("ADMIN", "PRECEPTOR", "DOCENTE", "DIRECTIVO")
    def asistencias():
        cursor = _cursor()
        rol = g.usuario["rol"]
        puede_cargar = rol in {"ADMIN", "PRECEPTOR", "DOCENTE"}
        try:
            if request.method == "POST":
                if not puede_cargar:
                    abort(403)
                _validar_csrf()
                try:
                    inscripcion_id = int(request.form.get("id_inscripcion", ""))
                    estado = request.form.get("estado", "")
                    fecha = normalizar_fecha(request.form.get("fecha_clase"), campo="fecha_clase", no_futura=True)
                    if estado not in {"PRESENTE", "AUSENTE", "JUSTIFICADO"} or not fecha.valido:
                        raise ValueError("Revise la fecha y el estado de asistencia.")
                    cursor.execute(
                        "SELECT id_materia, id_ciclo FROM inscripciones WHERE id_inscripcion = %s AND activo = TRUE",
                        (inscripcion_id,),
                    )
                    inscripcion = cursor.fetchone()
                    if not inscripcion:
                        raise ValueError("La inscripción no existe o está inactiva.")
                    if rol == "DOCENTE":
                        cursor.execute("SELECT id_docente FROM usuarios WHERE id_usuario = %s", (g.usuario["id_usuario"],))
                        cuenta = cursor.fetchone()
                        if not cuenta or not cuenta["id_docente"]:
                            abort(403)
                        cursor.execute(
                            "SELECT 1 FROM asignaciones_docentes WHERE id_docente=%s AND id_materia=%s AND id_ciclo=%s LIMIT 1",
                            (cuenta["id_docente"], inscripcion["id_materia"], inscripcion["id_ciclo"]),
                        )
                        if not cursor.fetchone():
                            abort(403)
                    cursor.execute(
                        "INSERT INTO asistencias (id_inscripcion, fecha_clase, estado, activo) VALUES (%s, %s, %s, TRUE) "
                        "ON DUPLICATE KEY UPDATE estado = VALUES(estado), activo = TRUE",
                        (inscripcion_id, fecha.valor, estado),
                    )
                    _db().commit()
                    flash("Asistencia guardada.", "success")
                    return redirect(url_for("asistencias"))
                except ValueError as error:
                    flash(str(error), "error")

            filtro_docente = ""
            parametros_docente: tuple[Any, ...] = ()
            if rol == "DOCENTE":
                filtro_docente = (
                    " AND EXISTS (SELECT 1 FROM usuarios u JOIN asignaciones_docentes ad ON ad.id_docente=u.id_docente "
                    "WHERE u.id_usuario=%s AND ad.id_materia=i.id_materia AND ad.id_ciclo=i.id_ciclo)"
                )
                parametros_docente = (g.usuario["id_usuario"],)
            cursor.execute(
                "SELECT i.id_inscripcion, a.legajo, a.apellido, a.nombre, m.codigo, c.anio "
                "FROM inscripciones i JOIN alumnos a ON a.id_alumno=i.id_alumno "
                "JOIN materias m ON m.id_materia=i.id_materia JOIN ciclos_lectivos c ON c.id_ciclo=i.id_ciclo "
                "WHERE i.activo=TRUE" + filtro_docente + " ORDER BY c.anio DESC, m.codigo, a.apellido, a.nombre",
                parametros_docente,
            )
            inscripciones = cursor.fetchall()
            cursor.execute(
                "SELECT i.id_inscripcion, a.legajo, a.apellido, a.nombre, m.codigo, c.anio, "
                "SUM(CASE WHEN x.estado='PRESENTE' THEN 1 ELSE 0 END) AS presentes, "
                "SUM(CASE WHEN x.estado='AUSENTE' THEN 1 ELSE 0 END) AS ausentes, "
                "SUM(CASE WHEN x.estado='JUSTIFICADO' THEN 1 ELSE 0 END) AS justificados "
                "FROM inscripciones i JOIN alumnos a ON a.id_alumno=i.id_alumno "
                "JOIN materias m ON m.id_materia=i.id_materia JOIN ciclos_lectivos c ON c.id_ciclo=i.id_ciclo "
                "LEFT JOIN asistencias x ON x.id_inscripcion=i.id_inscripcion AND x.activo=TRUE "
                "WHERE i.activo=TRUE" + filtro_docente + " "
                "GROUP BY i.id_inscripcion, a.legajo, a.apellido, a.nombre, m.codigo, c.anio "
                "ORDER BY c.anio DESC, m.codigo, a.apellido, a.nombre",
                parametros_docente,
            )
            resumen = cursor.fetchall()
            cursor.execute("SELECT valor FROM parametros WHERE clave='asistencia_minima'")
            minimo_row = cursor.fetchone()
            minimo = int(minimo_row["valor"]) if minimo_row and str(minimo_row["valor"]).isdigit() else None
            justificada_como_presente = False
        finally:
            cursor.close()

        for fila in resumen:
            total_base = fila["presentes"] + fila["ausentes"]
            consideradas = total_base + (fila["justificados"] if justificada_como_presente else 0)
            cuentan = fila["presentes"] + (fila["justificados"] if justificada_como_presente else 0)
            fila["porcentaje"] = round(100 * cuentan / consideradas, 1) if consideradas else None
            fila["cumple_minimo"] = minimo is None or fila["porcentaje"] is None or fila["porcentaje"] >= minimo
        return render_template(
            "asistencias.html", inscripciones=inscripciones, resumen=resumen,
            puede_cargar=puede_cargar, minimo=minimo, justificada_como_presente=justificada_como_presente,
        )

    @app.get("/plantillas/<nombre>")
    @requiere_roles("ADMIN", "PRECEPTOR")
    def descargar_plantilla(nombre: str):
        if nombre not in PLANTILLAS_CARGA:
            abort(404)
        return send_from_directory(CARPETA_PLANTILLAS, nombre, as_attachment=True)

    @app.get("/cargas/errores/<nombre>")
    @requiere_roles("ADMIN", "PRECEPTOR")
    def descargar_log(nombre: str):
        if not re.fullmatch(r"errores_masivas_[0-9T_-]+\.log", nombre):
            abort(404)
        return send_from_directory(CARPETA_LOGS, nombre, as_attachment=True)

    @app.route("/cargas", methods=["GET", "POST"])
    @requiere_roles("ADMIN", "PRECEPTOR")
    def cargas():
        if request.method == "GET":
            return render_template("cargas.html", plantillas=PLANTILLAS_CARGA.keys())

        _validar_csrf()
        archivo = request.files.get("archivo")
        if not archivo or not archivo.filename:
            flash("Seleccione una plantilla .xlsx.", "error")
            return redirect(url_for("cargas"))
        nombre_archivo = Path(archivo.filename).name
        nombre_plantilla = request.form.get("plantilla", "")
        if nombre_plantilla not in PLANTILLAS_CARGA or Path(nombre_archivo).suffix.lower() != ".xlsx":
            flash("Use una de las tres plantillas oficiales del SGMA.", "error")
            return redirect(url_for("cargas"))

        entidad, encabezados_esperados = PLANTILLAS_CARGA[nombre_plantilla]
        errores = RegistroErrores()
        try:
            libro = load_workbook(io.BytesIO(archivo.read()), read_only=True, data_only=True)
            if "Datos" not in libro.sheetnames:
                raise ValueError("Falta la hoja Datos.")
            hoja = libro["Datos"]
            filas = hoja.iter_rows(values_only=True)
            encabezados = tuple(str(v).strip() if v is not None else "" for v in next(filas))
            if encabezados != encabezados_esperados:
                errores.agregar(nombre_archivo, 1, "encabezados", "ERR_08_PLANTILLA", "Las columnas u orden no coinciden con la plantilla oficial.")
                log_path = CARPETA_LOGS / ("errores_masivas_" + datetime.now().strftime("%Y%m%dT%H%M%S") + ".log")
                errores.guardar(log_path)
                flash("Archivo rechazado antes de procesar filas: revise los encabezados.", "error")
                return redirect(url_for("descargar_log", nombre=log_path.name))
            datos = [
                (numero, dict(zip(encabezados, valores)))
                for numero, valores in enumerate(filas, start=2)
                if any(valor is not None and str(valor).strip() for valor in valores)
            ]
            libro.close()
        except Exception as error:
            flash(f"No se pudo leer el archivo .xlsx: {error}", "error")
            return redirect(url_for("cargas"))

        conexion = _db()
        cursor = _cursor()
        filas_ok = 0
        dnis_lote: set[str] = set()
        try:
            cursor.execute(
                "INSERT INTO lotes_carga (tipo, entidad, id_usuario, archivo, filas_total, filas_ok, filas_error) "
                "VALUES ('MASIVA', %s, %s, %s, %s, 0, 0)",
                (entidad, g.usuario["id_usuario"], nombre_archivo, len(datos)),
            )
            id_lote = cursor.lastrowid
            for numero_fila, registro in datos:
                cursor.execute("SAVEPOINT fila_carga")
                cantidad_errores_antes = len(errores.errores)
                try:
                    if entidad == "alumnos":
                        dni = normalizar_dni(registro.get("dni"), dnis_del_lote=dnis_lote)
                        apellido = normalizar_nombre(registro.get("apellido"), "apellido")
                        nombre = normalizar_nombre(registro.get("nombre"), "nombre")
                        email = normalizar_email(registro.get("email"))
                        fecha_texto = registro.get("fecha_nacimiento")
                        fecha = normalizar_fecha(fecha_texto, campo="fecha_nacimiento", no_futura=True) if fecha_texto else None
                        for resultado in (dni, apellido, nombre, email, fecha):
                            if resultado and not resultado.valido:
                                for error in resultado.errores:
                                    errores.agregar(nombre_archivo, numero_fila, error.campo, error.codigo, error.mensaje)
                        cursor.execute("SELECT id_alumno FROM alumnos WHERE dni=%s LIMIT 1", (dni.valor,)) if dni.valido else None
                        existente = cursor.fetchone() if dni.valido else None
                        if existente:
                            errores.agregar(nombre_archivo, numero_fila, "dni", "ERR_01_DNI_DUP", "El DNI ya existe en alumnos.")
                        carrera_nombre = str(registro.get("carrera") or "").strip()
                        try:
                            anio_ingreso = int(registro.get("anio_ingreso"))
                        except (TypeError, ValueError):
                            anio_ingreso = 0
                        cursor.execute("SELECT id_carrera FROM carreras WHERE LOWER(nombre)=LOWER(%s) AND activa=TRUE", (carrera_nombre,))
                        carrera = cursor.fetchone()
                        if not carrera:
                            errores.agregar(nombre_archivo, numero_fila, "carrera", "ERR_02_FK_NOTFOUND", "La carrera no existe o no está activa.")
                        if not 1900 <= anio_ingreso <= 2200:
                            errores.agregar(nombre_archivo, numero_fila, "anio_ingreso", None, "El año de ingreso no es válido.")
                        if len(errores.errores) == cantidad_errores_antes:
                            legajo = cursor.callproc("sp_proximo_legajo", [0])[0]
                            cursor.execute(
                                "INSERT INTO alumnos (legajo,dni,apellido,nombre,fecha_nacimiento,email,origen) VALUES (%s,%s,%s,%s,%s,%s,'MASIVA')",
                                (legajo, dni.valor, apellido.valor, nombre.valor, fecha.valor if fecha else None, email.valor),
                            )
                            id_alumno = cursor.lastrowid
                            cursor.execute(
                                "INSERT INTO matriculas (id_alumno,id_carrera,anio_ingreso) VALUES (%s,%s,%s)",
                                (id_alumno, carrera["id_carrera"], anio_ingreso),
                            )
                    elif entidad == "inscripciones":
                        dni = normalizar_dni(registro.get("dni_alumno"))
                        codigo = re.sub(r"[\s-]+", "", str(registro.get("codigo_materia") or "")).upper()
                        condicion = str(registro.get("condicion_cursada") or "CURSANDO").strip().upper()
                        try:
                            anio = int(registro.get("anio_ciclo"))
                        except (TypeError, ValueError):
                            anio = 0
                        if not dni.valido:
                            for error in dni.errores:
                                errores.agregar(nombre_archivo, numero_fila, error.campo, error.codigo, error.mensaje)
                        if condicion not in {"CURSANDO", "REGULAR", "PROMOCIONADO", "LIBRE"} or not 1900 <= anio <= 2200:
                            errores.agregar(nombre_archivo, numero_fila, "condicion_cursada", None, "Condición o año de ciclo inválido.")
                        cursor.execute("SELECT id_alumno FROM alumnos WHERE dni=%s AND activo=TRUE", (dni.valor,)) if dni.valido else None
                        alumno = cursor.fetchone() if dni.valido else None
                        cursor.execute("SELECT id_materia FROM materias WHERE codigo=%s AND activa=TRUE", (codigo,))
                        materia = cursor.fetchone()
                        cursor.execute("SELECT id_ciclo FROM ciclos_lectivos WHERE anio=%s", (anio,))
                        ciclo = cursor.fetchone()
                        if not alumno or not materia or not ciclo:
                            errores.agregar(nombre_archivo, numero_fila, "referencia", "ERR_02_FK_NOTFOUND", "No existe alumno, materia o ciclo lectivo.")
                        if len(errores.errores) == cantidad_errores_antes and alumno and materia and ciclo:
                            cursor.execute(
                                "SELECT cr.id_materia_requerida FROM correlatividades cr WHERE cr.id_materia=%s AND NOT EXISTS "
                                "(SELECT 1 FROM actas_examen ae WHERE ae.id_alumno=%s AND ae.id_materia=cr.id_materia_requerida AND ae.estado='APROBADO' AND ae.activo=TRUE)",
                                (materia["id_materia"], alumno["id_alumno"]),
                            )
                            if cursor.fetchone():
                                errores.agregar(nombre_archivo, numero_fila, "codigo_materia", "ERR_06_CORRELATIVA", "Faltan correlativas aprobadas.")
                            else:
                                cursor.execute(
                                    "INSERT INTO inscripciones (id_alumno,id_materia,id_ciclo,condicion_cursada) VALUES (%s,%s,%s,%s)",
                                    (alumno["id_alumno"], materia["id_materia"], ciclo["id_ciclo"], condicion),
                                )
                    else:
                        dni = normalizar_dni(registro.get("dni_alumno"))
                        codigo = re.sub(r"[\s-]+", "", str(registro.get("codigo_materia") or "")).upper()
                        fecha = normalizar_fecha(registro.get("fecha_examen"), campo="fecha_examen", no_futura=True)
                        condicion = str(registro.get("condicion") or "").strip().upper()
                        estados = {"APROBADO": "APROBADO", "AP": "APROBADO", "PROM": "APROBADO", "DESAPROBADO": "DESAPROBADO", "DES": "DESAPROBADO", "AUSENTE": "AUSENTE", "A": "AUSENTE"}
                        estado = estados.get(condicion)
                        nota_texto = str(registro.get("nota") or "").strip()
                        libro_texto = str(registro.get("libro") or "").strip()
                        folio_texto = str(registro.get("folio") or "").strip()
                        ausente = estado == "AUSENTE" or nota_texto.upper() in {"A", "AUSENTE"}
                        nota = None if ausente else normalizar_nota(nota_texto)
                        if not dni.valido:
                            for error in dni.errores:
                                errores.agregar(nombre_archivo, numero_fila, error.campo, error.codigo, error.mensaje)
                        if not fecha.valido:
                            for error in fecha.errores:
                                errores.agregar(nombre_archivo, numero_fila, error.campo, error.codigo, error.mensaje)
                        if not ausente and nota and not nota.valido:
                            for error in nota.errores:
                                errores.agregar(nombre_archivo, numero_fila, error.campo, error.codigo, error.mensaje)
                        if not estado:
                            errores.agregar(nombre_archivo, numero_fila, "condicion", None, "Condición de acta desconocida.")
                        if not libro_texto or len(libro_texto) > 20 or not folio_texto or len(folio_texto) > 20:
                            errores.agregar(nombre_archivo, numero_fila, "libro/folio", None, "Libro y folio son obligatorios y no pueden superar 20 caracteres.")
                        alumno = materia = None
                        if dni.valido:
                            cursor.execute("SELECT id_alumno FROM alumnos WHERE dni=%s AND activo=TRUE", (dni.valor,))
                            alumno = cursor.fetchone()
                        cursor.execute("SELECT id_materia FROM materias WHERE codigo=%s AND activa=TRUE", (codigo,))
                        materia = cursor.fetchone()
                        if not alumno or not materia:
                            errores.agregar(nombre_archivo, numero_fila, "referencia", "ERR_02_FK_NOTFOUND", "No existe alumno o materia.")
                        if len(errores.errores) == cantidad_errores_antes and alumno and materia:
                            cursor.execute(
                                "INSERT INTO actas_examen (id_alumno,id_materia,fecha_examen,libro,folio,nota,estado,origen,id_lote) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,'MASIVA',%s)",
                                (alumno["id_alumno"], materia["id_materia"], fecha.valor, libro_texto, folio_texto, nota.valor if nota else None, estado, id_lote),
                            )
                    if len(errores.errores) == cantidad_errores_antes:
                        filas_ok += 1
                        cursor.execute("RELEASE SAVEPOINT fila_carga")
                    else:
                        cursor.execute("ROLLBACK TO SAVEPOINT fila_carga")
                        cursor.execute("RELEASE SAVEPOINT fila_carga")
                        if entidad == "alumnos" and "dni" in locals() and dni.valido:
                            dnis_lote.discard(dni.valor)
                except mysql.connector.IntegrityError:
                    cursor.execute("ROLLBACK TO SAVEPOINT fila_carga")
                    cursor.execute("RELEASE SAVEPOINT fila_carga")
                    if entidad == "alumnos" and "dni" in locals() and dni.valido:
                        dnis_lote.discard(dni.valor)
                    codigo_error = "ERR_01_DNI_DUP" if entidad == "alumnos" else "VALIDACION"
                    errores.agregar(nombre_archivo, numero_fila, "registro", codigo_error, "Restricción de unicidad o integridad; se omitió la fila.")

            cursor.execute(
                "UPDATE lotes_carga SET filas_ok=%s, filas_error=%s WHERE id_lote=%s",
                (filas_ok, len(datos) - filas_ok, id_lote),
            )
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()

        if errores.errores:
            CARPETA_LOGS.mkdir(parents=True, exist_ok=True)
            log_path = CARPETA_LOGS / ("errores_masivas_" + datetime.now().strftime("%Y%m%dT%H%M%S") + ".log")
            errores.guardar(log_path)
            flash(f"Se importaron {filas_ok} filas; {len(datos) - filas_ok} filas fueron rechazadas. Descargar informe de errores.", "success")
            return redirect(url_for("descargar_log", nombre=log_path.name))
        flash(f"Carga completada: {filas_ok} filas procesadas.", "success")
        return redirect(url_for("cargas"))

    @app.get("/busqueda")
    @requiere_roles("ADMIN", "PRECEPTOR", "DIRECTIVO", "DOCENTE")
    def busqueda():
        cursor = _cursor()
        query = request.args.get("q", "").strip()
        resultados: list[dict[str, Any]] = []
        try:
            if query:
                cursor.execute(
                    "SELECT id_alumno, legajo, dni, apellido, nombre, fecha_nacimiento, email, activo "
                    "FROM alumnos WHERE dni=%s OR CAST(legajo AS CHAR)=%s ORDER BY apellido,nombre LIMIT 20",
                    (query, query),
                )
                alumnos_encontrados = cursor.fetchall()
                id_docente = None
                if g.usuario["rol"] == "DOCENTE":
                    cursor.execute("SELECT id_docente FROM usuarios WHERE id_usuario=%s", (g.usuario["id_usuario"],))
                    perfil = cursor.fetchone()
                    id_docente = perfil["id_docente"] if perfil else None

                for alumno in alumnos_encontrados:
                    if g.usuario["rol"] == "DOCENTE":
                        if not id_docente:
                            continue
                        cursor.execute(
                            "SELECT 1 FROM inscripciones i JOIN asignaciones_docentes ad "
                            "ON ad.id_materia=i.id_materia AND ad.id_ciclo=i.id_ciclo "
                            "WHERE i.id_alumno=%s AND i.activo=TRUE AND ad.id_docente=%s LIMIT 1",
                            (alumno["id_alumno"], id_docente),
                        )
                        if not cursor.fetchone():
                            continue

                    cursor.execute(
                        "SELECT c.nombre, m.anio_ingreso, m.estado FROM matriculas m "
                        "JOIN carreras c ON c.id_carrera=m.id_carrera WHERE m.id_alumno=%s ORDER BY m.anio_ingreso",
                        (alumno["id_alumno"],),
                    )
                    alumno["matriculas"] = cursor.fetchall()

                    consulta_notas = (
                        "SELECT n.instancia, n.nota, n.fecha, ma.codigo, ma.nombre AS materia "
                        "FROM notas_cursada n JOIN inscripciones i ON i.id_inscripcion=n.id_inscripcion "
                        "JOIN materias ma ON ma.id_materia=i.id_materia WHERE i.id_alumno=%s AND n.activo=TRUE"
                    )
                    if g.usuario["rol"] == "DOCENTE":
                        consulta_notas += " AND EXISTS (SELECT 1 FROM asignaciones_docentes ad WHERE ad.id_docente=%s AND ad.id_materia=i.id_materia AND ad.id_ciclo=i.id_ciclo)"
                        cursor.execute(consulta_notas + " ORDER BY n.fecha DESC", (alumno["id_alumno"], id_docente))
                    else:
                        cursor.execute(consulta_notas + " ORDER BY n.fecha DESC", (alumno["id_alumno"],))
                    notas = cursor.fetchall()

                    consulta_actas = (
                        "SELECT ae.nota, ae.estado, ae.fecha_examen, ae.libro, ae.folio, ma.codigo, ma.nombre AS materia "
                        "FROM actas_examen ae JOIN materias ma ON ma.id_materia=ae.id_materia "
                        "WHERE ae.id_alumno=%s AND ae.activo=TRUE"
                    )
                    if g.usuario["rol"] == "DOCENTE":
                        consulta_actas += (
                            " AND ae.id_mesa IS NOT NULL AND EXISTS (SELECT 1 FROM asignaciones_docentes ad "
                            "JOIN mesas_examen mx ON mx.id_materia=ad.id_materia AND mx.id_ciclo=ad.id_ciclo "
                            "WHERE ad.id_docente=%s AND mx.id_mesa=ae.id_mesa)"
                        )
                        cursor.execute(consulta_actas + " ORDER BY ae.fecha_examen DESC", (alumno["id_alumno"], id_docente))
                    else:
                        cursor.execute(consulta_actas + " ORDER BY ae.fecha_examen DESC", (alumno["id_alumno"],))
                    actas = cursor.fetchall()

                    notas_numericas = [Decimal(str(n["nota"])) for n in notas if n["nota"] is not None]
                    actas_numericas = [Decimal(str(a["nota"])) for a in actas if a["nota"] is not None]
                    todas = notas_numericas + actas_numericas
                    promedio = lambda valores: (sum(valores, Decimal("0")) / len(valores)).quantize(Decimal("0.01")) if valores else None
                    alumno["notas"] = notas
                    alumno["actas"] = actas
                    alumno["promedio_cursada"] = promedio(notas_numericas)
                    alumno["promedio_examenes"] = promedio(actas_numericas)
                    alumno["promedio_general"] = promedio(todas)
                    resultados.append(alumno)
        finally:
            cursor.close()
        return render_template("busqueda.html", busqueda=query, alumnos=resultados)

    def datos_analitico(id_alumno: int) -> dict[str, Any]:
        cursor = _cursor()
        try:
            cursor.execute(
                "SELECT id_alumno, legajo, dni, apellido, nombre, fecha_nacimiento, email, activo "
                "FROM alumnos WHERE id_alumno=%s",
                (id_alumno,),
            )
            alumno = cursor.fetchone()
            if not alumno:
                abort(404)
            cursor.execute(
                "SELECT c.nombre, m.anio_ingreso, m.estado FROM matriculas m "
                "JOIN carreras c ON c.id_carrera=m.id_carrera WHERE m.id_alumno=%s ORDER BY m.anio_ingreso",
                (id_alumno,),
            )
            matriculas = cursor.fetchall()
            cursor.execute(
                "SELECT ma.codigo, ma.nombre AS materia, n.instancia, n.nota, n.fecha "
                "FROM notas_cursada n JOIN inscripciones i ON i.id_inscripcion=n.id_inscripcion "
                "JOIN materias ma ON ma.id_materia=i.id_materia WHERE i.id_alumno=%s AND n.activo=TRUE ORDER BY n.fecha, ma.codigo",
                (id_alumno,),
            )
            notas = cursor.fetchall()
            cursor.execute(
                "SELECT ma.codigo, ma.nombre AS materia, ae.fecha_examen, ae.libro, ae.folio, ae.nota, ae.estado "
                "FROM actas_examen ae JOIN materias ma ON ma.id_materia=ae.id_materia "
                "WHERE ae.id_alumno=%s AND ae.activo=TRUE ORDER BY ae.fecha_examen, ma.codigo",
                (id_alumno,),
            )
            actas = cursor.fetchall()
            cursor.execute(
                "SELECT ma.codigo, ma.nombre AS materia, c.anio, x.fecha_clase, x.estado "
                "FROM asistencias x JOIN inscripciones i ON i.id_inscripcion=x.id_inscripcion "
                "JOIN materias ma ON ma.id_materia=i.id_materia JOIN ciclos_lectivos c ON c.id_ciclo=i.id_ciclo "
                "WHERE i.id_alumno=%s AND x.activo=TRUE ORDER BY c.anio, ma.codigo, x.fecha_clase",
                (id_alumno,),
            )
            asistencias = cursor.fetchall()
            cursor.execute(
                "SELECT AVG(n.nota) AS promedio FROM notas_cursada n JOIN inscripciones i ON i.id_inscripcion=n.id_inscripcion "
                "WHERE i.id_alumno=%s AND n.activo=TRUE",
                (id_alumno,),
            )
            promedio_cursada = cursor.fetchone()["promedio"]
            cursor.execute("SELECT AVG(nota) AS promedio FROM actas_examen WHERE id_alumno=%s AND activo=TRUE", (id_alumno,))
            promedio_examenes = cursor.fetchone()["promedio"]
            cursor.execute(
                "SELECT AVG(nota) AS promedio FROM ("
                "SELECT n.nota FROM notas_cursada n JOIN inscripciones i ON i.id_inscripcion=n.id_inscripcion WHERE i.id_alumno=%s AND n.activo=TRUE "
                "UNION ALL SELECT ae.nota FROM actas_examen ae WHERE ae.id_alumno=%s AND ae.activo=TRUE) calificaciones",
                (id_alumno, id_alumno),
            )
            promedio_general = cursor.fetchone()["promedio"]
            cursor.execute("SELECT valor FROM parametros WHERE clave='asistencia_minima'")
            minimo_row = cursor.fetchone()
            minimo = int(minimo_row["valor"]) if minimo_row and str(minimo_row["valor"]).isdigit() else None
            asistencias_por_materia: dict[tuple[str, int], list[str]] = {}
            for asistencia in asistencias:
                clave = (asistencia["codigo"], asistencia["anio"])
                asistencias_por_materia.setdefault(clave, []).append(asistencia["estado"])
            resumen_asistencia = []
            for (codigo, anio), estados in sorted(asistencias_por_materia.items()):
                presentes = estados.count("PRESENTE")
                ausentes = estados.count("AUSENTE")
                justificadas = estados.count("JUSTIFICADO")
                denominador = presentes + ausentes
                porcentaje = round(100 * presentes / denominador, 1) if denominador else None
                resumen_asistencia.append({
                    "codigo": codigo,
                    "anio": anio,
                    "presentes": presentes,
                    "ausentes": ausentes,
                    "justificadas": justificadas,
                    "porcentaje": porcentaje,
                    "cumple": minimo is None or porcentaje is None or porcentaje >= minimo,
                })
            return {
                "alumno": alumno, "matriculas": matriculas, "notas": notas, "actas": actas,
                "asistencias": asistencias, "resumen_asistencia": resumen_asistencia,
                "promedio_cursada": promedio_cursada, "promedio_examenes": promedio_examenes,
                "promedio_general": promedio_general, "minimo_asistencia": minimo,
            }
        finally:
            cursor.close()

    @app.get("/reportes/alumnos/<int:id_alumno>/analitico.pdf")
    @requiere_roles("ADMIN", "PRECEPTOR", "DIRECTIVO")
    def exportar_analitico_pdf(id_alumno: int):
        from html import escape
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, LongTable

        datos = datos_analitico(id_alumno)
        alumno = datos["alumno"]
        salida = io.BytesIO()
        documento = SimpleDocTemplate(salida, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
        estilos = getSampleStyleSheet()
        estilos.add(ParagraphStyle(name="TituloSGMA", parent=estilos["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#12345a")))
        elementos = [
            Paragraph("Certificado analítico", estilos["TituloSGMA"]),
            Paragraph("Sistema de Gestión y Migración Académica", estilos["Normal"]),
            Spacer(1, 8),
            Paragraph(f"<b>Alumno:</b> {escape(alumno['apellido'])}, {escape(alumno['nombre'])}", estilos["Normal"]),
            Paragraph(f"<b>Legajo:</b> {alumno['legajo']} &nbsp;&nbsp; <b>DNI:</b> {escape(alumno['dni'])}", estilos["Normal"]),
            Paragraph(f"<b>Estado:</b> {'Activo' if alumno['activo'] else 'Inactivo'}", estilos["Normal"]),
            Paragraph(f"<b>Promedio cursada:</b> {datos['promedio_cursada'] or '—'} &nbsp;&nbsp; <b>Promedio exámenes:</b> {datos['promedio_examenes'] or '—'} &nbsp;&nbsp; <b>Combinado:</b> {datos['promedio_general'] or '—'}", estilos["Normal"]),
            Spacer(1, 8),
        ]
        elementos.append(Paragraph("Matrículas", estilos["Heading2"]))
        matriculas = [["Carrera", "Ingreso", "Estado"]] + [[m["nombre"], str(m["anio_ingreso"]), m["estado"]] for m in datos["matriculas"]]
        elementos.append(Table(matriculas, repeatRows=1, hAlign="LEFT", style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dce8f5")), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#aebdce")),
            ("PADDING", (0,0), (-1,-1), 5),
        ])))
        elementos.append(Paragraph("Notas de cursada", estilos["Heading2"]))
        filas_notas = [["Materia", "Instancia", "Nota", "Fecha"]] + [[f"{n['codigo']} · {n['materia']}", n["instancia"], str(n["nota"]), str(n["fecha"])] for n in datos["notas"]]
        elementos.append(LongTable(filas_notas, colWidths=[68*mm, 48*mm, 22*mm, 32*mm], repeatRows=1, hAlign="LEFT", style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dce8f5")), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#aebdce")), ("PADDING", (0,0), (-1,-1), 5),
        ])))
        elementos.append(Paragraph("Actas de examen", estilos["Heading2"]))
        filas_actas = [["Materia", "Fecha", "Nota", "Estado", "Libro/Folio"]] + [[f"{a['codigo']} · {a['materia']}", str(a["fecha_examen"]), str(a["nota"]) if a["nota"] is not None else "—", a["estado"], f"{a['libro']}/{a['folio']}"] for a in datos["actas"]]
        elementos.append(LongTable(filas_actas, colWidths=[58*mm, 28*mm, 20*mm, 35*mm, 29*mm], repeatRows=1, hAlign="LEFT", style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dce8f5")), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#aebdce")), ("PADDING", (0,0), (-1,-1), 4),
        ])))
        elementos.append(Paragraph("Asistencia por materia", estilos["Heading2"]))
        filas_asistencia = [["Materia", "Ciclo", "Presentes", "Ausentes", "Justificadas", "%"]] + [[r["codigo"], str(r["anio"]), str(r["presentes"]), str(r["ausentes"]), str(r["justificadas"]), f"{r['porcentaje']}%" if r["porcentaje"] is not None else "—"] for r in datos["resumen_asistencia"]]
        elementos.append(LongTable(filas_asistencia, colWidths=[50*mm, 20*mm, 25*mm, 24*mm, 30*mm, 20*mm], repeatRows=1, hAlign="LEFT", style=TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dce8f5")), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#aebdce")), ("PADDING", (0,0), (-1,-1), 4),
        ])))
        elementos.append(Spacer(1, 6))
        elementos.append(Paragraph(f"Umbral de asistencia configurado: {datos['minimo_asistencia'] if datos['minimo_asistencia'] is not None else 'sin configurar'}%. Justificadas excluidas del denominador.", estilos["Italic"]))
        documento.build(elementos)
        salida.seek(0)
        return send_file(salida, mimetype="application/pdf", as_attachment=True, download_name=f"analitico_legajo_{alumno['legajo']}.pdf")

    @app.get("/reportes/alumnos/<int:id_alumno>/analitico.xlsx")
    @requiere_roles("ADMIN", "PRECEPTOR", "DIRECTIVO")
    def exportar_analitico_excel(id_alumno: int):
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill

        datos = datos_analitico(id_alumno)
        alumno = datos["alumno"]
        libro = Workbook()
        resumen = libro.active
        resumen.title = "Resumen"
        resumen.append(["Certificado analítico SGMA"])
        resumen.append(["Legajo", alumno["legajo"]])
        resumen.append(["DNI", alumno["dni"]])
        resumen.append(["Apellido y nombre", f"{alumno['apellido']}, {alumno['nombre']}"])
        resumen.append(["Estado", "Activo" if alumno["activo"] else "Inactivo"])
        resumen.append(["Promedio cursada", float(datos["promedio_cursada"]) if datos["promedio_cursada"] is not None else None])
        resumen.append(["Promedio exámenes", float(datos["promedio_examenes"]) if datos["promedio_examenes"] is not None else None])
        resumen.append(["Promedio combinado", float(datos["promedio_general"]) if datos["promedio_general"] is not None else None])
        resumen.append(["Umbral de asistencia", datos["minimo_asistencia"]])
        resumen.append(["Regla de asistencia", "JUSTIFICADO excluido del denominador"])
        resumen.append([])
        resumen.append(["Carrera", "Año de ingreso", "Estado de matrícula"])
        for matricula in datos["matriculas"]:
            resumen.append([matricula["nombre"], matricula["anio_ingreso"], matricula["estado"]])

        def agregar_hoja(nombre: str, encabezados: list[str], registros: list[list[Any]]) -> None:
            hoja = libro.create_sheet(nombre)
            hoja.append(encabezados)
            for registro in registros:
                hoja.append(registro)
            hoja.freeze_panes = "A2"
            hoja.auto_filter.ref = hoja.dimensions
            for celda in hoja[1]:
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = PatternFill("solid", fgColor="12345A")
            for columna in hoja.columns:
                ancho = min(42, max(12, max((len(str(c.value or "")) for c in columna), default=0) + 2))
                hoja.column_dimensions[columna[0].column_letter].width = ancho

        agregar_hoja("Notas cursada", ["Código", "Materia", "Instancia", "Nota", "Fecha"], [[n["codigo"], n["materia"], n["instancia"], float(n["nota"]), n["fecha"]] for n in datos["notas"]])
        agregar_hoja("Actas", ["Código", "Materia", "Fecha", "Nota", "Estado", "Libro", "Folio"], [[a["codigo"], a["materia"], a["fecha_examen"], float(a["nota"]) if a["nota"] is not None else None, a["estado"], a["libro"], a["folio"]] for a in datos["actas"]])
        agregar_hoja("Asistencias", ["Código", "Materia", "Ciclo", "Presentes", "Ausentes", "Justificadas", "% asistencia"], [[r["codigo"], next((a["materia"] for a in datos["asistencias"] if a["codigo"] == r["codigo"]), ""), r["anio"], r["presentes"], r["ausentes"], r["justificadas"], r["porcentaje"]] for r in datos["resumen_asistencia"]])
        resumen.column_dimensions["A"].width = 28
        resumen.column_dimensions["B"].width = 40
        for celda in resumen[1]:
            celda.font = Font(bold=True, size=14, color="12345A")
        salida = io.BytesIO()
        libro.save(salida)
        salida.seek(0)
        return send_file(salida, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=f"analitico_legajo_{alumno['legajo']}.xlsx")

    @app.get("/reportes/alumnos.xlsx")
    @requiere_roles("ADMIN", "PRECEPTOR", "DIRECTIVO")
    def exportar_reporte_alumnos():
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill

        cursor = _cursor()
        try:
            cursor.execute(
                "SELECT a.id_alumno, a.legajo, a.dni, a.apellido, a.nombre, "
                "GROUP_CONCAT(DISTINCT c.nombre ORDER BY c.nombre SEPARATOR ', ') AS carreras "
                "FROM alumnos a LEFT JOIN matriculas m ON m.id_alumno=a.id_alumno "
                "LEFT JOIN carreras c ON c.id_carrera=m.id_carrera WHERE a.activo=TRUE "
                "GROUP BY a.id_alumno,a.legajo,a.dni,a.apellido,a.nombre ORDER BY a.apellido,a.nombre"
            )
            alumnos_reporte = cursor.fetchall()
            cursor.execute("SELECT valor FROM parametros WHERE clave='asistencia_minima'")
            minimo_row = cursor.fetchone()
            minimo = int(minimo_row["valor"]) if minimo_row and str(minimo_row["valor"]).isdigit() else None
            libro = Workbook()
            hoja = libro.active
            hoja.title = "Reporte alumnos"
            hoja.append(["Legajo", "DNI", "Apellido", "Nombre", "Carreras", "Promedio cursada", "Promedio exámenes", "Promedio combinado", "% asistencia"])
            for alumno in alumnos_reporte:
                cursor.execute(
                    "SELECT AVG(n.nota) AS promedio FROM notas_cursada n JOIN inscripciones i ON i.id_inscripcion=n.id_inscripcion "
                    "WHERE i.id_alumno=%s AND n.activo=TRUE",
                    (alumno["id_alumno"],),
                )
                promedio_cursada = cursor.fetchone()["promedio"]
                cursor.execute("SELECT AVG(nota) AS promedio FROM actas_examen WHERE id_alumno=%s AND activo=TRUE", (alumno["id_alumno"],))
                promedio_examenes = cursor.fetchone()["promedio"]
                cursor.execute(
                    "SELECT AVG(nota) AS promedio FROM (SELECT n.nota FROM notas_cursada n JOIN inscripciones i ON i.id_inscripcion=n.id_inscripcion WHERE i.id_alumno=%s AND n.activo=TRUE "
                    "UNION ALL SELECT nota FROM actas_examen WHERE id_alumno=%s AND activo=TRUE) notas",
                    (alumno["id_alumno"], alumno["id_alumno"]),
                )
                promedio_general = cursor.fetchone()["promedio"]
                cursor.execute(
                    "SELECT SUM(CASE WHEN x.estado='PRESENTE' THEN 1 ELSE 0 END) AS presentes, "
                    "SUM(CASE WHEN x.estado='AUSENTE' THEN 1 ELSE 0 END) AS ausentes "
                    "FROM inscripciones i LEFT JOIN asistencias x ON x.id_inscripcion=i.id_inscripcion AND x.activo=TRUE "
                    "WHERE i.id_alumno=%s AND i.activo=TRUE",
                    (alumno["id_alumno"],),
                )
                asistencia = cursor.fetchone()
                presentes, ausentes = asistencia["presentes"] or 0, asistencia["ausentes"] or 0
                total = presentes + ausentes
                porcentaje = round(100 * presentes / total, 1) if total else None
                hoja.append([
                    alumno["legajo"], alumno["dni"], alumno["apellido"], alumno["nombre"], alumno["carreras"],
                    float(promedio_cursada) if promedio_cursada is not None else None,
                    float(promedio_examenes) if promedio_examenes is not None else None,
                    float(promedio_general) if promedio_general is not None else None,
                    porcentaje,
                ])
            hoja.freeze_panes = "A2"
            hoja.auto_filter.ref = hoja.dimensions
            for celda in hoja[1]:
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = PatternFill("solid", fgColor="12345A")
            for columna in hoja.columns:
                hoja.column_dimensions[columna[0].column_letter].width = min(40, max(12, max((len(str(c.value or "")) for c in columna), default=0) + 2))
            salida = io.BytesIO()
            libro.save(salida)
            salida.seek(0)
        finally:
            cursor.close()
        return send_file(salida, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name="reporte_academico_alumnos.xlsx")

    return app


app = create_app()
