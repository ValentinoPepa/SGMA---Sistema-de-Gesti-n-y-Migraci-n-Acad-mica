"""B1: smoke-walk the live SGMA routes against the real QA/operational DB.

Starts a loopback-only WSGI server, logs in with temporary accounts for
ADMIN/PRECEPTOR/DOCENTE, checks route access, and verifies that a real app
write is audited with the authenticated user id. Temporary accounts and the
temporary teacher are deactivated during cleanup; no student or grade is added.
"""

from __future__ import annotations

import os
import re
import secrets
import sys
import threading
import http.cookiejar
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

import mysql.connector
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server


TARGET_DB = "gestion_academica_v2"
ROLES = ("ADMIN", "PRECEPTOR", "DOCENTE")
COMMON_PAGES = ("/", "/alumnos", "/carreras", "/materias", "/ciclos",
                "/cursadas", "/asistencias", "/busqueda")


def configure_environment() -> None:
    if os.getenv("SGMA_DB_NAME", TARGET_DB) != TARGET_DB:
        raise RuntimeError(f"Detenido: B1 solo permite {TARGET_DB}.")
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


def create_fixtures(run_tag: str, password: str):
    conn = connect()
    user_ids: dict[str, int] = {}
    teacher_id = None
    try:
        cur = conn.cursor()
        cur.execute("SELECT VERSION(), DATABASE()")
        version, database = cur.fetchone()
        if database != TARGET_DB:
            raise RuntimeError(f"Base inesperada: {database}.")
        cur.execute(
            "SELECT u.id_usuario FROM usuarios u JOIN roles r ON r.id_rol=u.id_rol "
            "WHERE u.activo=TRUE AND r.nombre='ADMIN' ORDER BY u.id_usuario LIMIT 1"
        )
        existing_admin = cur.fetchone()
        if not existing_admin:
            raise RuntimeError("La base no tiene una cuenta ADMIN activa para registrar las fixtures.")
        cur.execute("SET @app_user_id=%s", (existing_admin[0],))
        cur.execute(
            "INSERT INTO docentes (nombre,apellido,dni,email) VALUES (%s,%s,%s,%s)",
            ("B1", "Temporal", f"{secrets.randbelow(100_000_000):08d}", f"b1-{run_tag.lower()}@example.invalid"),
        )
        teacher_id = int(cur.lastrowid)
        cur.execute("SELECT nombre,id_rol FROM roles WHERE nombre IN ('ADMIN','PRECEPTOR','DOCENTE')")
        role_ids = {name: int(role_id) for name, role_id in cur.fetchall()}
        if set(role_ids) != set(ROLES):
            raise RuntimeError("Faltan roles requeridos en la base.")
        password_hash = generate_password_hash(password)
        for role in ROLES:
            username = f"b1_{role.lower()}_{run_tag.lower()}"
            cur.execute(
                "INSERT INTO usuarios (username,password_hash,id_rol,id_docente) VALUES (%s,%s,%s,%s)",
                (username, password_hash, role_ids[role], teacher_id if role == "DOCENTE" else None),
            )
            user_ids[role] = int(cur.lastrowid)
        conn.commit()
        return str(version), user_ids, teacher_id, {r: f"b1_{r.lower()}_{run_tag.lower()}" for r in ROLES}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    if not match:
        raise RuntimeError("El formulario no contiene token CSRF.")
    return match.group(1)


class HttpSession:
    def __init__(self):
        self.opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(self, url: str, data: dict[str, str] | None = None, timeout: int = 15):
        payload = urlencode(data).encode() if data is not None else None
        request = Request(url, data=payload, method="POST" if data is not None else "GET")
        try:
            response = self.opener.open(request, timeout=timeout)
            return type("Response", (), {"status_code": response.status, "text": response.read().decode(errors="replace")})()
        except HTTPError as error:
            return type("Response", (), {"status_code": error.code, "text": error.read().decode(errors="replace")})()

    def get(self, url: str, timeout: int = 15):
        return self.request(url, timeout=timeout)

    def post(self, url: str, data: dict[str, str], timeout: int = 15):
        return self.request(url, data=data, timeout=timeout)


def login(base_url: str, username: str, password: str) -> HttpSession:
    session = HttpSession()
    page = session.get(base_url + "/login", timeout=10)
    token = csrf_token(page.text)
    response = session.post(
        base_url + "/login",
        data={"csrf_token": token, "username": username, "password": password},
        timeout=10,
    )
    if response.status_code != 200 or session.get(base_url + "/", timeout=10).status_code != 200:
        raise RuntimeError(f"Falló el inicio de sesión para el rol asociado a {username}.")
    return session


def request_page(session: HttpSession, base_url: str, path: str) -> int:
    return session.get(base_url + path, timeout=15).status_code


def record_access_checks(base_url: str, usernames: dict[str, str], password: str):
    results: list[tuple[str, str, int, int]] = []
    sessions = {role: login(base_url, usernames[role], password) for role in ROLES}
    role_pages = {
        "ADMIN": {"/docentes": 200, "/usuarios": 200, "/cargas": 200},
        "PRECEPTOR": {"/docentes": 200, "/usuarios": 403, "/cargas": 200},
        "DOCENTE": {"/docentes": 403, "/usuarios": 403, "/cargas": 403},
    }
    for role, session in sessions.items():
        for path in COMMON_PAGES:
            expected = 200
            actual = request_page(session, base_url, path)
            results.append((role, path, actual, expected))
        for path, expected in role_pages[role].items():
            actual = request_page(session, base_url, path)
            results.append((role, path, actual, expected))
    docente_html = sessions["DOCENTE"].get(base_url + "/alumnos", timeout=15).text
    for field in ("DNI", "E-mail"):
        actual = 1 if field in docente_html else 0
        results.append(("DOCENTE", f"datos ocultos: {field}", actual, 0))
    admin_post = sessions["ADMIN"].post(
        base_url + "/alumnos", data={"accion": "crear"}, timeout=15
    )
    results.append(("ADMIN", "POST /alumnos (solo lectura)", admin_post.status_code, 403))
    failures = [item for item in results if item[2] != item[3]]
    return results, failures, sessions


def verify_app_user_id(session: HttpSession, base_url: str, preceptor_id: int, admin_id: int) -> None:
    page = session.get(base_url + "/usuarios", timeout=15)
    token = csrf_token(page.text)
    response = session.post(
        base_url + "/usuarios",
        data={"csrf_token": token, "accion": "desactivar", "usuario_id": str(preceptor_id)},
        timeout=15,
    )
    if response.status_code != 200:
        raise RuntimeError(f"La desactivación de la cuenta temporal respondió HTTP {response.status_code}.")
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id_usuario FROM auditoria WHERE tabla='usuarios' AND operacion='UPDATE' "
            "AND id_registro=%s AND campo='activo' ORDER BY id_evento DESC LIMIT 1",
            (preceptor_id,),
        )
        row = cur.fetchone()
        if not row or int(row[0]) != admin_id:
            raise RuntimeError(f"La auditoría no atribuyó el cambio al ADMIN autenticado (esperado {admin_id}, evento {row}).")
    finally:
        conn.close()


def cleanup(user_ids: dict[str, int], teacher_id: int | None) -> None:
    if not user_ids and teacher_id is None:
        return
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SET @app_user_id=%s", (user_ids.get("ADMIN"),))
        if user_ids:
            cur.executemany("UPDATE usuarios SET activo=FALSE WHERE id_usuario=%s",
                            [(uid,) for uid in user_ids.values()])
        if teacher_id is not None:
            cur.execute("UPDATE docentes SET activo=FALSE WHERE id_docente=%s", (teacher_id,))
        conn.commit()
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
    run_tag = secrets.token_hex(5)
    password = secrets.token_urlsafe(18)
    user_ids: dict[str, int] = {}
    teacher_id = None
    server = None
    thread = None
    try:
        version, user_ids, teacher_id, usernames = create_fixtures(run_tag, password)
        from sgma.web import app

        server = make_server("127.0.0.1", 0, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        results, failures, sessions = record_access_checks(base_url, usernames, password)
        verify_app_user_id(sessions["ADMIN"], base_url, user_ids["PRECEPTOR"], user_ids["ADMIN"])
        for role, path, actual, expected in results:
            print(f"{role} {path}: HTTP {actual} (esperado {expected})")
        print(f"Motor/base: {version} / {TARGET_DB}")
        print("Auditoría @app_user_id: OK; id_usuario coincide con el ADMIN autenticado")
        print(f"Fallos: {len(failures)}")
        for role, path, actual, expected in failures:
            print(f"FALLA {role} {path}: observado={actual}, esperado={expected}")
        return 1 if failures else 0
    finally:
        if server is not None:
            server.shutdown()
        if thread is not None:
            thread.join(timeout=5)
        cleanup(user_ids, teacher_id)


if __name__ == "__main__":
    raise SystemExit(main())
