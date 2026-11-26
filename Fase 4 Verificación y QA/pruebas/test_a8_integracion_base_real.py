"""A8: repeat a 5,000-row upload and panel permission checks on the QA DB.

This is an integration test: Flask routes and mysql.connector use the real
database. It refuses any database other than gestion_academica_rnf02.
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

import mysql.connector
from openpyxl import load_workbook
from werkzeug.security import generate_password_hash


TARGET_DB = "gestion_academica_rnf02"
ROWS = 5_000
RUN_TAG = secrets.token_hex(5).upper()
PASSWORD = secrets.token_urlsafe(20)


def connect():
    return mysql.connector.connect(
        host=os.environ["SGMA_DB_HOST"],
        port=int(os.environ.get("SGMA_DB_PORT", "3306")),
        user=os.environ["SGMA_DB_USER"],
        password=os.environ.get("SGMA_DB_PASSWORD", ""),
        database=TARGET_DB,
        autocommit=False,
    )


def check_target() -> tuple[str, int]:
    if os.getenv("SGMA_DB_NAME", TARGET_DB) != TARGET_DB:
        raise RuntimeError(f"Detenido: A8 solo se permite en {TARGET_DB}.")
    os.environ["SGMA_DB_NAME"] = TARGET_DB
    os.environ.setdefault("SGMA_DB_HOST", "127.0.0.1")
    os.environ.setdefault("SGMA_DB_USER", "root")
    os.environ.setdefault("SGMA_DB_PASSWORD", "")
    os.environ.setdefault("SGMA_DB_PORT", "3306")
    os.environ.setdefault("SGMA_SECRET_KEY", secrets.token_urlsafe(32))
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT VERSION(), DATABASE()")
        version, database = cur.fetchone()
        if database != TARGET_DB:
            raise RuntimeError(f"Base inesperada: {database!r}.")
        cur.execute("SELECT COUNT(*) FROM actas_examen")
        initial = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM alumnos WHERE activo=TRUE")
        students = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM materias WHERE activa=TRUE")
        subjects = int(cur.fetchone()[0])
        if not students or not subjects:
            raise RuntimeError("La base QA no tiene alumnos y materias activas para la carga.")
        return str(version), initial
    finally:
        conn.close()


def create_test_users() -> dict[str, tuple[int, str]]:
    users: dict[str, tuple[int, str]] = {}
    conn = connect()
    try:
        cur = conn.cursor()
        for role in ("ADMIN", "PRECEPTOR", "DIRECTIVO"):
            cur.execute("SELECT id_rol FROM roles WHERE nombre=%s", (role,))
            role_row = cur.fetchone()
            if not role_row:
                raise RuntimeError(f"No existe el rol {role} en el esquema QA.")
            username = f"a8_{role.lower()}_{RUN_TAG.lower()}"
            cur.execute(
                "INSERT INTO usuarios (username,password_hash,id_rol) VALUES (%s,%s,%s)",
                (username, generate_password_hash(PASSWORD), role_row[0]),
            )
            users[role] = (int(cur.lastrowid), username)
        conn.commit()
        return users
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def csrf_from(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    if not match:
        raise RuntimeError("No se encontró token CSRF en el formulario.")
    return match.group(1)


def login_as(client, username: str) -> None:
    page = client.get("/login")
    token = csrf_from(page.get_data(as_text=True))
    response = client.post(
        "/login", data={"csrf_token": token, "username": username, "password": PASSWORD},
        follow_redirects=True,
    )
    if response.status_code != 200 or b"Sesion iniciada" not in response.data and b"Sesi" not in response.data:
        # Verify the authenticated session through a route, avoiding dependence
        # on the template's accent encoding.
        check = client.get("/cargas")
        if check.status_code in (302, 401):
            raise RuntimeError(f"No se pudo iniciar sesión para {username}.")


def check_permissions(users: dict[str, tuple[int, str]]) -> None:
    from sgma.web import app

    app.config.update(TESTING=True)
    for role, expected in (("ADMIN", 200), ("PRECEPTOR", 200), ("DIRECTIVO", 403)):
        client = app.test_client()
        login_as(client, users[role][1])
        response = client.get("/cargas")
        if response.status_code != expected:
            raise RuntimeError(f"Permisos /cargas: {role} devolvió {response.status_code}, esperado {expected}.")


def workbook_bytes(template: Path) -> io.BytesIO:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT dni FROM alumnos WHERE activo=TRUE ORDER BY id_alumno")
        dnis = [str(row[0]) for row in cur.fetchall()]
        cur.execute("SELECT codigo FROM materias WHERE activa=TRUE ORDER BY id_materia")
        codes = [str(row[0]) for row in cur.fetchall()]
    finally:
        conn.close()
    book = load_workbook(template)
    sheet = book["Datos"]
    expected = ("dni_alumno", "codigo_materia", "fecha_examen", "libro", "folio", "nota", "condicion")
    headers = tuple(str(cell.value).strip() if cell.value is not None else "" for cell in sheet[1])
    if headers != expected:
        raise RuntimeError(f"Encabezados inesperados en Plantilla_Actas.xlsx: {headers!r}")
    for index in range(ROWS):
        sheet.append((dnis[index % len(dnis)], codes[(index // len(dnis)) % len(codes)],
                      date(2025, 12, 1), f"A8{RUN_TAG}", f"{index + 1:08d}", 8, "APROBADO"))
    out = io.BytesIO()
    book.save(out)
    out.seek(0)
    return out


def upload_5000(preceptor: tuple[int, str], template: Path) -> tuple[float, int, tuple[int, int, int]]:
    from sgma.web import app

    client = app.test_client()
    login_as(client, preceptor[1])
    page = client.get("/cargas")
    if page.status_code != 200:
        raise RuntimeError(f"PRECEPTOR no pudo abrir /cargas: HTTP {page.status_code}.")
    token = csrf_from(page.get_data(as_text=True))
    upload_name = f"A8_{RUN_TAG}_5000.xlsx"
    start = time.perf_counter()
    response = client.post(
        "/cargas",
        data={"csrf_token": token, "plantilla": "Plantilla_Actas.xlsx",
              "archivo": (workbook_bytes(template), upload_name)},
        content_type="multipart/form-data", follow_redirects=True,
    )
    elapsed = time.perf_counter() - start
    html = response.get_data(as_text=True)
    if response.status_code != 200 or "Carga completada: 5000 filas procesadas." not in html:
        raise RuntimeError(f"POST real de carga no completado (HTTP {response.status_code}).")

    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM actas_examen WHERE libro=%s", (f"A8{RUN_TAG}",))
        added = int(cur.fetchone()[0])
        cur.execute(
            "SELECT filas_total,filas_ok,filas_error FROM lotes_carga "
            "WHERE tipo='MASIVA' AND entidad='actas_examen' AND archivo=%s ORDER BY id_lote DESC LIMIT 1",
            (upload_name,),
        )
        lot = cur.fetchone()
        cur.close()
    finally:
        conn.close()
    if added != ROWS or not lot or tuple(map(int, lot)) != (ROWS, ROWS, 0):
        raise RuntimeError(f"Verificación post carga no coincide: actas={added}, lote={lot}.")
    return elapsed, added, tuple(map(int, lot))


def main() -> int:
    version, initial = check_target()
    project = Path(__file__).resolve().parents[2]
    code_dir = next(project.glob("Fase 3*/codigo"))
    sys.path.insert(0, str(code_dir))
    users: dict[str, tuple[int, str]] = {}
    try:
        users = create_test_users()
        check_permissions(users)
        template = next(project.glob("Fase 2*/Plantilla_Actas.xlsx"))
        elapsed, added, lot = upload_5000(users["PRECEPTOR"], template)
        conn = connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM actas_examen")
            final = int(cur.fetchone()[0])
        finally:
            conn.close()
        if final != initial + added:
            raise RuntimeError(f"Conteo total inesperado: antes={initial}, después={final}.")
        print(f"Motor/base: MariaDB {version} / {TARGET_DB}")
        print("Permisos GET /cargas: ADMIN=200, PRECEPTOR=200, DIRECTIVO=403")
        print(f"Carga POST real: {added} filas válidas; lote total/ok/error={lot[0]}/{lot[1]}/{lot[2]}")
        print(f"Actas antes/después: {initial}/{final}")
        print(f"Tiempo del POST de 5.000 filas: {elapsed:.3f} s (objetivo RNF-10: <120 s)")
        print("Resultado RNF-10:", "CUMPLE" if elapsed < 120 else "NO CUMPLE")
        return 0
    finally:
        if users:
            conn = connect()
            try:
                cur = conn.cursor()
                cur.executemany("UPDATE usuarios SET activo=FALSE WHERE id_usuario=%s",
                                [(user_id,) for user_id, _ in users.values()])
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
