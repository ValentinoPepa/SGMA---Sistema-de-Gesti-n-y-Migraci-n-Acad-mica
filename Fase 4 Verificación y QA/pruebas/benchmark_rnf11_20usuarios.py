"""RNF-11 concurrency check against the isolated SGMA QA database.

Runs 20 distinct authenticated Flask sessions concurrently. It checks parallel
student creation and simultaneous requests against the same record. The app
currently only exposes logical deactivation, not versioned record editing.
"""

from __future__ import annotations

import os
import re
import secrets
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


TARGET_DB = "gestion_academica_rnf02"
USERS = 20


def configure_environment() -> None:
    if os.getenv("SGMA_DB_NAME", TARGET_DB) != TARGET_DB:
        raise RuntimeError(f"Test stopped: only {TARGET_DB} is permitted.")
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


def create_test_users() -> list[tuple[int, str, str]]:
    from werkzeug.security import generate_password_hash

    conn = connect_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_rol FROM roles WHERE nombre='PRECEPTOR'")
        role = cur.fetchone()
        if not role:
            raise RuntimeError("The QA schema has no PRECEPTOR role.")
        created: list[tuple[int, str, str]] = []
        for _ in range(USERS):
            username = "c4_rnf11_" + secrets.token_hex(6)
            password = secrets.token_urlsafe(32)
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, id_rol) VALUES (%s,%s,%s)",
                (username, generate_password_hash(password), role["id_rol"]),
            )
            created.append((int(cur.lastrowid), username, password))
        conn.commit()
        cur.close()
        return created
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def unique_test_dnis() -> list[str]:
    conn = connect_db()
    try:
        cur = conn.cursor()
        while True:
            values = list({str(10_000_000 + secrets.randbelow(89_999_999)) for _ in range(USERS)})
            if len(values) != USERS:
                continue
            marks = ",".join(["%s"] * len(values))
            cur.execute(f"SELECT dni FROM alumnos WHERE dni IN ({marks})", values)
            if not cur.fetchall():
                return values
    finally:
        cur.close()
        conn.close()


def qa_counts() -> tuple[str, int, int]:
    conn = connect_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT VERSION(), DATABASE()")
        version, database = cur.fetchone()
        if database != TARGET_DB:
            raise RuntimeError(f"Safety check failed: connected to {database}.")
        cur.execute("SELECT COUNT(*) FROM actas_examen")
        acts = int(cur.fetchone()[0])
        cur.close()
        return str(version), acts, database
    finally:
        conn.close()


def authenticated_client(app, user: tuple[int, str, str], page_path: str):
    client = app.test_client()
    login_page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', login_page.get_data(as_text=True))
    if login_page.status_code != 200 or not token:
        raise RuntimeError("Could not load login form/CSRF token.")
    response = client.post(
        "/login",
        data={"csrf_token": token.group(1), "username": user[1], "password": user[2]},
        follow_redirects=False,
    )
    if response.status_code != 302:
        raise RuntimeError("A temporary QA account could not authenticate.")
    page = client.get(page_path)
    page_html = page.get_data(as_text=True)
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', page_html)
    version = re.search(r'name="version" value="([0-9]+)"', page_html)
    if page.status_code != 200 or not csrf:
        raise RuntimeError(f"Authenticated session could not load {page_path}.")
    return client, csrf.group(1), int(version.group(1)) if version else None


def run_parallel(app, users, form_factory, *, page_path="/alumnos", follow_redirects=True):
    started = [0.0]

    def mark_start() -> None:
        started[0] = time.perf_counter()

    barrier = threading.Barrier(USERS, action=mark_start)

    def submit(index: int):
        user = users[index]
        client, csrf, version = authenticated_client(app, user, page_path)
        payload = {"csrf_token": csrf, **form_factory(index, version)}
        barrier.wait(timeout=60)
        item_start = time.perf_counter()
        response = client.post(page_path, data=payload, follow_redirects=follow_redirects)
        elapsed = time.perf_counter() - item_start
        return response.status_code, elapsed, response.get_data(as_text=True)

    with ThreadPoolExecutor(max_workers=USERS) as pool:
        futures = [pool.submit(submit, index) for index in range(USERS)]
        results = [future.result(timeout=180) for future in futures]
    wall = time.perf_counter() - started[0]
    return (
        wall,
        [elapsed for _, elapsed, _ in results],
        [status for status, _, _ in results],
        [body for _, _, body in results],
    )


def verify_created_students(dnis: list[str]) -> list[dict]:
    conn = connect_db()
    try:
        cur = conn.cursor(dictionary=True)
        marks = ",".join(["%s"] * len(dnis))
        cur.execute(
            f"SELECT id_alumno, dni, legajo, activo FROM alumnos WHERE dni IN ({marks})",
            dnis,
        )
        rows = cur.fetchall()
        if len(rows) != USERS or len({int(row["legajo"]) for row in rows}) != USERS:
            raise RuntimeError(f"Lost or duplicate concurrent student creation: {len(rows)} rows.")
        cur.close()
        return rows
    finally:
        conn.close()


def verify_edited_version(row_id: int) -> tuple[int, str, int]:
    conn = connect_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT version, apellido FROM alumnos WHERE id_alumno=%s", (row_id,))
        row = cur.fetchone()
        cur.execute(
            "SELECT COUNT(*) AS cantidad FROM auditoria WHERE tabla='alumnos' AND operacion='UPDATE' "
            "AND id_registro=%s AND campo='apellido'",
            (row_id,),
        )
        audit = int(cur.fetchone()["cantidad"])
        cur.close()
        if not row:
            raise RuntimeError("The edited QA student disappeared.")
        return int(row["version"]), str(row["apellido"]), audit
    finally:
        conn.close()


def deactivate_qa_rows(dnis: list[str], user_ids: list[int]) -> None:
    conn = connect_db()
    try:
        cur = conn.cursor()
        if dnis:
            marks = ",".join(["%s"] * len(dnis))
            cur.execute(f"UPDATE alumnos SET activo=FALSE WHERE dni IN ({marks})", dnis)
        if user_ids:
            marks = ",".join(["%s"] * len(user_ids))
            cur.execute(f"UPDATE usuarios SET activo=FALSE WHERE id_usuario IN ({marks})", user_ids)
        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> int:
    configure_environment()
    project = Path(__file__).resolve().parents[2]
    code_dir = next(project.glob("Fase 3*/codigo"))
    sys.path.insert(0, str(code_dir))
    version, existing_acts, database = qa_counts()
    users = create_test_users()
    dnis: list[str] = []

    try:
        dnis = unique_test_dnis()
        from sgma.web import app

        app.config.update(TESTING=True)
        create_wall, create_latencies, create_statuses, create_bodies = run_parallel(
            app,
            users,
            lambda index, _version: {
                "accion": "crear",
                "dni": dnis[index],
                "apellido": f"QAConcurrente{index:02d}",
                "nombre": "Prueba",
                "fecha_nacimiento": "",
                "email": "",
            },
        )
        if any(status != 200 for status in create_statuses) or any(
            "Alumno creado con legajo" not in body for body in create_bodies
        ):
            raise RuntimeError("Not all concurrent create requests reported success.")
        rows = verify_created_students(dnis)
        target_id = int(rows[0]["id_alumno"])

        edit_wall, edit_latencies, edit_statuses, _edit_bodies = run_parallel(
            app,
            users,
            lambda index, version: {
                "version": str(version),
                "dni": rows[0]["dni"],
                "apellido": f"Editado{index:02d}",
                "nombre": "Prueba",
                "fecha_nacimiento": "",
                "email": "",
            },
            page_path=f"/alumnos/{target_id}/editar",
            follow_redirects=False,
        )
        successes = edit_statuses.count(302)
        conflicts = edit_statuses.count(409)
        if successes != 1 or conflicts != USERS - 1:
            raise RuntimeError(f"Expected 1 successful update and {USERS - 1} conflicts; got {edit_statuses}.")
        conflict_pages = sum(
            status == 409 and "Conflicto de" in body
            for status, body in zip(edit_statuses, _edit_bodies)
        )
        if conflict_pages != conflicts:
            raise RuntimeError("Some stale edits did not show the conflict message.")
        final_version, final_surname, audit_events = verify_edited_version(target_id)
        expected_surnames = {f"Editado{index:02d}" for index in range(USERS)}
        if final_version != 2 or final_surname not in expected_surnames or audit_events != 1:
            raise RuntimeError(
                f"Unexpected final version/name/audit: {final_version}/{final_surname}/{audit_events}."
            )

        print(f"Motor: {version}")
        print(f"Base aislada: {database}; actas de referencia: {existing_acts:,}")
        print(f"Usuarios QA autenticados en sesiones distintas: {USERS}")
        print(f"Concurrent student inserts: {USERS}/{USERS}; unique legajos: {len({int(row['legajo']) for row in rows})}")
        print(f"Tiempo total altas (POST + respuesta): {create_wall:.3f} s")
        print(f"Individual insert latency: median {statistics.median(create_latencies):.3f} s; max {max(create_latencies):.3f} s")
        print(f"Concurrent edits to the same student: {USERS}")
        print(f"Concurrent edit requests total: {edit_wall:.3f} s")
        print(f"HTTP result: {successes} saved, {conflicts} conflicts (409)")
        print(f"Final version: {final_version}; saved surname: {final_surname}")
        print(f"Audit events for the saved surname change: {audit_events}")
        print("RNF-11 result: stale edits were detected and rejected.")
        print("Alcance: Flask test client con 20 sesiones autenticadas en paralelo; sin red externa.")
        return 0
    finally:
        deactivate_qa_rows(dnis, [int(user[0]) for user in users])


if __name__ == "__main__":
    raise SystemExit(main())
