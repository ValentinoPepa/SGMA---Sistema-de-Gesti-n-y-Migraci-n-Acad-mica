"""B2 integration check: define a correlation and block enrollment with ERR_06.

Uses the real MariaDB connection to the isolated gestion_academica_a1_qa
schema. Temporary test users, one cycle, and one correlation are cleaned up.
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

import mysql.connector
from werkzeug.security import generate_password_hash


TARGET_DB = "gestion_academica_a1_qa"


def configure_environment() -> None:
    if os.getenv("SGMA_DB_NAME", TARGET_DB) != TARGET_DB:
        raise RuntimeError(f"Detenido: B2 solo permite {TARGET_DB}.")
    os.environ["SGMA_DB_NAME"] = TARGET_DB
    os.environ.setdefault("SGMA_DB_HOST", "127.0.0.1")
    os.environ.setdefault("SGMA_DB_USER", "root")
    os.environ.setdefault("SGMA_DB_PASSWORD", "")
    os.environ.setdefault("SGMA_DB_PORT", "3306")
    os.environ.setdefault("SGMA_SECRET_KEY", secrets.token_urlsafe(32))


def connect():
    return mysql.connector.connect(
        host=os.environ["SGMA_DB_HOST"],
        port=int(os.environ["SGMA_DB_PORT"]),
        user=os.environ["SGMA_DB_USER"],
        password=os.environ.get("SGMA_DB_PASSWORD", ""),
        database=TARGET_DB,
        autocommit=False,
    )


def prepare_fixture(run_tag: str):
    conn = connect()
    user_ids: list[int] = []
    cycle_id = None
    correlation: tuple[int, int] | None = None
    student_dni = None
    target_code = None
    cycle_year = None
    try:
        cur = conn.cursor()
        cur.execute("SELECT VERSION(), DATABASE()")
        version, database = cur.fetchone()
        if database != TARGET_DB:
            raise RuntimeError(f"Base inesperada: {database}.")

        cur.execute(
            "SELECT a.id_alumno, a.dni, objetivo.id_materia, objetivo.codigo, "
            "requerida.id_materia, requerida.codigo "
            "FROM alumnos a "
            "JOIN materias objetivo ON objetivo.activa=TRUE "
            "JOIN materias requerida ON requerida.id_carrera=objetivo.id_carrera "
            "AND requerida.activa=TRUE AND requerida.id_materia<>objetivo.id_materia "
            "WHERE a.activo=TRUE "
            "AND NOT EXISTS (SELECT 1 FROM actas_examen ae WHERE ae.id_alumno=a.id_alumno "
            "AND ae.id_materia=requerida.id_materia AND ae.estado='APROBADO' AND ae.activo=TRUE) "
            "AND NOT EXISTS (SELECT 1 FROM correlatividades cr WHERE cr.id_materia=objetivo.id_materia "
            "AND cr.id_materia_requerida=requerida.id_materia) "
            "ORDER BY a.id_alumno, objetivo.id_materia, requerida.id_materia LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("No se encontró alumno/materias QA para probar una correlativa pendiente.")
        student_id, student_dni, target_id, target_code, required_id, _required_code = row
        correlation = (int(target_id), int(required_id))

        cur.execute("SELECT anio FROM ciclos_lectivos")
        used_years = {int(item[0]) for item in cur.fetchall()}
        cycle_year = next((year for year in range(2090, 2200) if year not in used_years), None)
        if cycle_year is None:
            raise RuntimeError("No hay un año libre de prueba en ciclos_lectivos.")
        cur.execute(
            "INSERT INTO ciclos_lectivos (anio,fecha_inicio,fecha_fin) VALUES (%s,%s,%s)",
            (cycle_year, f"{cycle_year}-01-01", f"{cycle_year}-12-31"),
        )
        cycle_id = int(cur.lastrowid)

        cur.execute("SELECT id_rol FROM roles WHERE nombre='ADMIN'")
        admin_role = cur.fetchone()
        cur.execute("SELECT id_rol FROM roles WHERE nombre='PRECEPTOR'")
        preceptor_role = cur.fetchone()
        if not admin_role or not preceptor_role:
            raise RuntimeError("Falta ADMIN o PRECEPTOR en el esquema QA.")
        for role, role_row in (("admin", admin_role), ("preceptor", preceptor_role)):
            username = f"b2_{role}_{run_tag}"
            cur.execute(
                "INSERT INTO usuarios (username,password_hash,id_rol) VALUES (%s,%s,%s)",
                (username, generate_password_hash(secrets.token_urlsafe(24)), int(role_row[0])),
            )
            user_ids.append(int(cur.lastrowid))
        conn.commit()
        return (
            str(version),
            int(student_id),
            str(student_dni),
            int(target_id),
            str(target_code),
            int(required_id),
            int(cycle_id),
            int(cycle_year),
            tuple(user_ids),
            correlation,
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def cleanup(cycle_id: int | None, correlation: tuple[int, int] | None, user_ids: tuple[int, ...]) -> None:
    conn = connect()
    try:
        cur = conn.cursor()
        if cycle_id is not None:
            cur.execute("DELETE FROM inscripciones WHERE id_ciclo=%s", (cycle_id,))
        if correlation is not None:
            cur.execute(
                "DELETE FROM correlatividades WHERE id_materia=%s AND id_materia_requerida=%s",
                correlation,
            )
        if cycle_id is not None:
            cur.execute("DELETE FROM ciclos_lectivos WHERE id_ciclo=%s", (cycle_id,))
        if user_ids:
            cur.executemany("UPDATE usuarios SET activo=FALSE WHERE id_usuario=%s", [(uid,) for uid in user_ids])
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> int:
    configure_environment()
    project = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(next(project.glob("Fase 3*/codigo"))))
    run_tag = secrets.token_hex(5)
    cycle_id = None
    correlation = None
    user_ids: tuple[int, ...] = ()
    try:
        (version, student_id, student_dni, target_id, target_code, required_id,
         cycle_id, cycle_year, user_ids_list, correlation) = prepare_fixture(run_tag)
        user_ids = tuple(user_ids_list)

        from sgma.web import create_app

        app = create_app({"TESTING": True, "SECRET_KEY": secrets.token_urlsafe(32)})
        preceptor = app.test_client()
        with preceptor.session_transaction() as session:
            session["usuario_id"] = user_ids[1]
            session["csrf"] = "b2-csrf-token"

        page = preceptor.get("/correlatividades")
        if page.status_code != 200 or b"Definir correlativa" not in page.data:
            raise RuntimeError(f"PRECEPTOR no pudo abrir la pantalla: HTTP {page.status_code}.")
        created = preceptor.post(
            "/correlatividades",
            data={
                "csrf_token": "b2-csrf-token",
                "id_materia": str(target_id),
                "id_materia_requerida": str(required_id),
            },
            follow_redirects=True,
        )
        if created.status_code != 200 or b"Correlativa definida." not in created.data:
            raise RuntimeError("La pantalla no guardó la correlativa de prueba.")
        if target_code.encode() not in created.data:
            raise RuntimeError("La correlativa guardada no aparece en el listado de la pantalla.")
        cycle_attempt = preceptor.post(
            "/correlatividades",
            data={
                "csrf_token": "b2-csrf-token",
                "id_materia": str(required_id),
                "id_materia_requerida": str(target_id),
            },
            follow_redirects=True,
        )
        if cycle_attempt.status_code != 200 or "genera un ciclo" not in cycle_attempt.get_data(as_text=True):
            raise RuntimeError("La pantalla no rechazó una correlativa circular.")

        admin = app.test_client()
        with admin.session_transaction() as session:
            session["usuario_id"] = user_ids[0]
            session["csrf"] = "b2-csrf-token"
        admin_page = admin.get("/correlatividades")
        if admin_page.status_code != 200 or b"Esta pantalla es de consulta" not in admin_page.data:
            raise RuntimeError("ADMIN no obtuvo la vista de solo consulta.")
        denied = admin.post(
            "/correlatividades",
            data={
                "csrf_token": "b2-csrf-token",
                "id_materia": str(target_id),
                "id_materia_requerida": str(required_id),
            },
        )
        if denied.status_code != 403:
            raise RuntimeError(f"ADMIN pudo modificar correlatividades: HTTP {denied.status_code}.")

        attempted = preceptor.post(
            "/cursadas",
            data={
                "csrf_token": "b2-csrf-token",
                "accion": "inscribir_cursada",
                "dni": student_dni,
                "codigo_materia": target_code,
                "anio_ciclo": str(cycle_year),
                "condicion_cursada": "CURSANDO",
            },
            follow_redirects=True,
        )
        if b"ERR_06_CORRELATIVA" not in attempted.data:
            raise RuntimeError("La inscripción sin correlativa aprobada no mostró ERR_06_CORRELATIVA.")

        conn = connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM inscripciones WHERE id_alumno=%s AND id_materia=%s AND id_ciclo=%s",
                (student_id, target_id, cycle_id),
            )
            inserted = int(cur.fetchone()[0])
            if inserted:
                raise RuntimeError("Se creó una inscripción pese a faltar la materia aprobada.")
            cur.execute(
                "SELECT COUNT(*) FROM correlatividades WHERE id_materia=%s AND id_materia_requerida=%s",
                correlation,
            )
            defined = int(cur.fetchone()[0])
            if defined != 1:
                raise RuntimeError(f"La correlativa guardada no está en la base: cantidad={defined}.")
        finally:
            conn.close()

        print(f"Motor/base QA: {version} / {TARGET_DB}")
        print("Pantalla PRECEPTOR: HTTP 200; la regla aparece en el listado")
        print("Correlativa circular: rechazada")
        print("Pantalla ADMIN: HTTP 200 solo consulta; POST de modificación HTTP 403")
        print("Inscripción sin acta aprobada de la correlativa: bloqueada con ERR_06_CORRELATIVA")
        print("Filas de inscripción creadas: 0")
        print("Resultado B2: CUMPLE")
        return 0
    finally:
        cleanup(cycle_id, correlation, user_ids)


if __name__ == "__main__":
    raise SystemExit(main())
