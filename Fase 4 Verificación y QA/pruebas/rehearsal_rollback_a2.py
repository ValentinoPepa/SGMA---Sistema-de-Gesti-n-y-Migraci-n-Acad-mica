"""A2 rollback rehearsal for an isolated, empty QA schema.

Run from the codigo directory after creating an ADMIN in gestion_academica_a2_qa.
The wrapper raises immediately after the second real acta insert. The ETL must roll
back the students, catalogs, lots, actas and trigger audit rows from that transaction.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = next(path / "codigo" for path in PROJECT_ROOT.iterdir() if path.is_dir() and path.name.startswith("Fase 3 "))
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from sgma import etl
from sgma.errores import RegistroErrores

TABLES = ("carreras", "materias", "alumnos", "lotes_carga", "actas_examen", "auditoria")


class RollbackEnsayo(Exception):
    pass


class CursorProxy:
    def __init__(self, cursor):
        self._cursor = cursor
        self.actas_insertadas = 0

    def execute(self, operation, params=None):
        result = self._cursor.execute(operation, params)
        if operation.lstrip().upper().startswith("INSERT INTO ACTAS_EXAMEN"):
            self.actas_insertadas += 1
            if self.actas_insertadas == 2:
                raise RollbackEnsayo("Fallo controlado despues de dos inserts de acta.")
        return result

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class ConnectionProxy:
    def __init__(self, connection):
        self._connection = connection
        self.cursor_proxy = None

    def cursor(self, *args, **kwargs):
        self.cursor_proxy = CursorProxy(self._connection.cursor(*args, **kwargs))
        return self.cursor_proxy

    def __getattr__(self, name):
        return getattr(self._connection, name)


def counts():
    connection = etl._conexion_mysql()
    try:
        cursor = connection.cursor()
        try:
            result = {}
            for table in TABLES:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result[table] = int(cursor.fetchone()[0])
            return result
        finally:
            cursor.close()
    finally:
        connection.close()


def main():
    database = os.getenv("SGMA_DB_NAME", "")
    if database != "gestion_academica_a2_qa":
        raise SystemExit("Safety stop: set SGMA_DB_NAME=gestion_academica_a2_qa first.")
    raw_admin_id = os.getenv("SGMA_MIGRACION_USER_ID", "").strip()
    if not raw_admin_id.isdigit() or int(raw_admin_id) < 1:
        raise SystemExit("Set SGMA_MIGRACION_USER_ID to the active ADMIN id.")

    before = counts()
    if any(before[name] for name in ("carreras", "materias", "alumnos", "lotes_carga", "actas_examen")):
        raise SystemExit("Safety stop: QA schema must have no migration data before rehearsal.")

    errors = RegistroErrores()
    alumnos, carreras, materias, actas = etl.preparar(errors)
    total_alumnos, total_plan, total_actas = etl._totales_fuente()
    real_factory = etl._conexion_mysql
    proxy_holder = {}

    def wrapped_factory():
        proxy = ConnectionProxy(real_factory())
        proxy_holder["connection"] = proxy
        return proxy

    etl._conexion_mysql = wrapped_factory
    try:
        etl.aplicar(
            alumnos, carreras, materias, actas, total_actas, errors,
            total_alumnos=total_alumnos,
            total_plan=total_plan,
            admin_user_id=int(raw_admin_id),
        )
    except RollbackEnsayo:
        proxy = proxy_holder.get("connection")
        attempted = proxy.cursor_proxy.actas_insertadas if proxy and proxy.cursor_proxy else 0
        if attempted != 2:
            raise SystemExit(f"Rollback trigger count unexpected: {attempted} acta inserts.")
    finally:
        etl._conexion_mysql = real_factory

    after = counts()
    if before != after:
        raise SystemExit(f"FAIL: table counts changed: before={before}; after={after}")
    print("ROLLBACK_OK: controlled failure after two acta inserts; all table counts unchanged.")
    print("The isolated QA schema is ready for the real A2 apply.")


if __name__ == "__main__":
    main()