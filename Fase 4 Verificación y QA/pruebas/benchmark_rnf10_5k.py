"""End-to-end C4/RNF-10 test of the official Actas mass-upload route.

Uses the Flask application and a dedicated test database. The workbook is
generated in memory from currently loaded QA students and subjects. This test
never targets gestion_academica_v2 and refuses an unexpected database state.
"""

from __future__ import annotations

import io
import os
import re
import secrets
import sys
import time
from datetime import date
from pathlib import Path

from openpyxl import load_workbook


TARGET_DB = "gestion_academica_rnf02"
ROWS = 5_000
UPLOAD_NAME = "c4_rnf10_5000.xlsx"


def configure_environment() -> None:
    if os.getenv("SGMA_DB_NAME", TARGET_DB) != TARGET_DB:
        raise RuntimeError(f"Prueba detenida: solo admite {TARGET_DB}.")
    os.environ["SGMA_DB_NAME"] = TARGET_DB
    os.environ.setdefault("SGMA_DB_HOST", "127.0.0.1")
    os.environ.setdefault("SGMA_DB_USER", "root")
    os.environ.setdefault("SGMA_DB_PASSWORD", "")
    os.environ.setdefault("SGMA_DB_PORT", "3306")
    os.environ.setdefault("SGMA_SECRET_KEY", secrets.token_urlsafe(32))


def connect_db():
    import mysql.connector

    return mysql.connector.connect(
        host=os.environ["SGMA_DB_HOST"],
        port=int(os.environ["SGMA_DB_PORT"]),
        user=os.environ["SGMA_DB_USER"],
        password=os.environ["SGMA_DB_PASSWORD"],
        database=TARGET_DB,
        autocommit=False,
    )


def qa_state() -> tuple[str, int, int, int]:
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT VERSION()")
        version = str(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM actas_examen")
        actas = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM lotes_carga WHERE tipo='MIGRACION' AND entidad='actas_examen'")
        migration_lots = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM alumnos WHERE activo=TRUE")
        students = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM materias WHERE activa=TRUE")
        subjects = int(cur.fetchone()[0])
        cur.close()
        if actas != 50_000 or migration_lots != 1 or not students or not subjects:
            raise RuntimeError(
                "La base QA no coincide con el punto de partida esperado "
                f"(actas={actas}, lotes_migracion={migration_lots}, alumnos={students}, materias={subjects}); "
                "no se realizó ninguna carga."
            )
        return version, students, subjects, actas
    finally:
        conn.close()


def find_or_create_admin() -> int:
    """Use an existing active admin or create a non-login benchmark account."""
    from werkzeug.security import generate_password_hash

    conn = connect_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT u.id_usuario FROM usuarios u JOIN roles r ON r.id_rol=u.id_rol "
            "WHERE r.nombre='ADMIN' AND u.activo=TRUE ORDER BY u.id_usuario LIMIT 1"
        )
        row = cur.fetchone()
        if row:
            conn.rollback()
            return int(row["id_usuario"])
        cur.execute("SELECT id_rol FROM roles WHERE nombre='ADMIN'")
        role = cur.fetchone()
        if not role:
            raise RuntimeError("No existe el rol ADMIN en el esquema QA.")
        username = "c4_rnf10_" + secrets.token_hex(5)
        random_password = secrets.token_urlsafe(32)
        cur.execute(
            "INSERT INTO usuarios (username, password_hash, id_rol) VALUES (%s, %s, %s)",
            (username, generate_password_hash(random_password), role["id_rol"]),
        )
        user_id = int(cur.lastrowid)
        conn.commit()
        return user_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def build_workbook(template: Path) -> io.BytesIO:
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT dni FROM alumnos WHERE activo=TRUE ORDER BY id_alumno")
        dnis = [str(row[0]) for row in cur.fetchall()]
        cur.execute("SELECT codigo FROM materias WHERE activa=TRUE ORDER BY id_materia")
        codes = [str(row[0]) for row in cur.fetchall()]
        cur.close()
    finally:
        conn.close()
    if not dnis or not codes:
        raise RuntimeError("La base QA no tiene alumnos o materias activas para generar las filas.")

    workbook = load_workbook(template)
    if "Datos" not in workbook.sheetnames:
        raise RuntimeError("La plantilla oficial no contiene la hoja Datos.")
    sheet = workbook["Datos"]
    headers = tuple(
        str(cell.value).strip() if cell.value is not None else ""
        for cell in sheet[1]
    )
    expected = ("dni_alumno", "codigo_materia", "fecha_examen", "libro", "folio", "nota", "condicion")
    if headers != expected:
        raise RuntimeError(f"Los encabezados de la plantilla cambiaron: {headers!r}")

    for index in range(ROWS):
        dni = dnis[index % len(dnis)]
        subject = codes[(index // len(dnis)) % len(codes)]
        sheet.append((dni, subject, date(2025, 12, 1), "C4RNF10", f"{index + 1:08d}", 8, "APROBADO"))
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def main() -> int:
    configure_environment()
    project = Path(__file__).resolve().parents[2]
    code_dir = next(project.glob("Fase 3*/codigo"))
    sys.path.insert(0, str(code_dir))

    version, student_count, subject_count, initial_actas = qa_state()
    admin_id = find_or_create_admin()
    template = next(project.glob("Fase 2*/Plantilla_Actas.xlsx"))
    upload = build_workbook(template)

    from sgma.web import app

    app.config.update(TESTING=True)
    client = app.test_client()
    with client.session_transaction() as session:
        session["usuario_id"] = admin_id
        session["csrf"] = secrets.token_urlsafe(32)

    page = client.get("/cargas")
    match = re.search(r'name="csrf_token" value="([^"]+)"', page.get_data(as_text=True))
    if page.status_code != 200 or not match:
        raise RuntimeError("No se pudo abrir el formulario autenticado de carga masiva.")

    start = time.perf_counter()
    response = client.post(
        "/cargas",
        data={
            "csrf_token": match.group(1),
            "plantilla": "Plantilla_Actas.xlsx",
            "archivo": (upload, UPLOAD_NAME),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    elapsed = time.perf_counter() - start
    html = response.get_data(as_text=True)
    if response.status_code != 200 or "Carga completada: 5000 filas procesadas." not in html:
        raise RuntimeError(
            "La carga no terminó con éxito; revisar respuesta HTTP y log de errores antes de interpretar el tiempo."
        )

    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM actas_examen")
        final_actas = int(cur.fetchone()[0])
        cur.execute(
            "SELECT filas_total, filas_ok, filas_error FROM lotes_carga "
            "WHERE tipo='MASIVA' AND entidad='actas_examen' AND archivo=%s ORDER BY id_lote DESC LIMIT 1",
            (UPLOAD_NAME,),
        )
        lot = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) FROM auditoria WHERE tabla='actas_examen' AND operacion='INSERT'"
        )
        audit_count = int(cur.fetchone()[0])
        cur.close()
    finally:
        conn.close()

    if final_actas != initial_actas + ROWS or not lot or tuple(int(x) for x in lot) != (ROWS, ROWS, 0):
        raise RuntimeError(f"La verificación de filas no coincide: final={final_actas}, lote={lot}.")

    print(f"Motor: {version}")
    print(f"Base aislada: {TARGET_DB}")
    print(f"Filas de plantilla: {ROWS:,}")
    print(f"Alumnos/materias de referencia: {student_count}/{subject_count}")
    print(f"Tiempo del POST de carga (validación + escritura + COMMIT): {elapsed:.3f} s")
    print(f"Actas antes/después: {initial_actas:,}/{final_actas:,}")
    print(f"Lote masivo (total/ok/error): {lot[0]}/{lot[1]}/{lot[2]}")
    print(f"Eventos de auditoría de actas acumulados: {audit_count:,}")
    print("Objetivo RNF-10: menos de 120 s")
    print("Resultado: CUMPLE" if elapsed < 120 else "Resultado: NO CUMPLE")
    print("Nota: se midió el flujo Flask en test client; no incluye latencia de red externa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
